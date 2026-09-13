#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Travel Album Generator CLI
Automates scanning, EXIF extraction, clustering into spots, media optimization,
QR code creation, and building a responsive web album with sidebar and lightbox.
"""

import os
import sys
import json
import argparse
import shutil
import urllib.parse
from datetime import datetime
from PIL import Image, ImageOps

def parse_exif_datetime(dt_str):
    if not dt_str:
        return None
    for fmt in ("%Y:%m:%d %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S"):
        try:
            return datetime.strptime(dt_str.strip(), fmt)
        except Exception:
            continue
    return None

def extract_exif(img_path):
    info = {"datetime": None, "lat": None, "lon": None}
    try:
        with Image.open(img_path) as img:
            exif = img.getexif()
            if not exif:
                return info
            dt = exif.get(36867) or exif.get(306)
            if dt:
                info["datetime"] = str(dt)
            
            gps_ifd = exif.get_ifd(0x8825)
            if gps_ifd:
                def to_deg(coord, ref):
                    if not coord or len(coord) < 3:
                        return None
                    d = float(coord[0])
                    m = float(coord[1])
                    s = float(coord[2])
                    val = d + (m / 60.0) + (s / 3600.0)
                    if ref in ['S', 'W']:
                        val = -val
                    return val
                lat = to_deg(gps_ifd.get(2), gps_ifd.get(1))
                lon = to_deg(gps_ifd.get(4), gps_ifd.get(3))
                if lat and lon:
                    info["lat"] = round(lat, 6)
                    info["lon"] = round(lon, 6)
    except Exception:
        pass
    return info

def cmd_scan(args):
    """Scan directory and cluster media into spots."""
    input_dir = args.input_dir
    output_json = args.output
    threshold_min = args.cluster_threshold_minutes

    extensions = ('.jpg', '.jpeg', '.png', '.mp4', '.mov')
    media_files = []
    
    for root, _, files in os.walk(input_dir):
        if any(skip in root for skip in ["VOID", "originals", "thumb", "web", ".git", ".agents"]):
            continue
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in extensions:
                media_files.append(os.path.join(root, f))
                
    print(f"Scanning {len(media_files)} files in {input_dir}...")
    
    records = []
    for p in media_files:
        fn = os.path.basename(p)
        ext = os.path.splitext(fn)[1].lower()
        is_video = ext in ('.mp4', '.mov')
        
        exif_info = {"datetime": None, "lat": None, "lon": None}
        if not is_video:
            exif_info = extract_exif(p)
            
        dt_val = None
        if exif_info["datetime"]:
            dt_val = parse_exif_datetime(exif_info["datetime"])
        if not dt_val:
            import re
            m = re.search(r'(20\d{2})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})', fn)
            if m:
                dt_str = f"{m.group(1)}:{m.group(2)}:{m.group(3)} {m.group(4)}:{m.group(5)}:{m.group(6)}"
                dt_val = parse_exif_datetime(dt_str)
                exif_info["datetime"] = dt_str
                
        if not dt_val:
            mtime = os.path.getmtime(p)
            dt_val = datetime.fromtimestamp(mtime)
            exif_info["datetime"] = dt_val.strftime("%Y:%m:%d %H:%M:%S")

        records.append({
            "filepath": p,
            "filename": fn,
            "type": "video" if is_video else "image",
            "dt": dt_val,
            "datetime": exif_info["datetime"],
            "lat": exif_info["lat"],
            "lon": exif_info["lon"]
        })
        
    records.sort(key=lambda x: x["dt"])
    
    spots = []
    letters = [chr(i) for i in range(ord('A'), ord('Z')+1)]
    current_items = []
    last_dt = None
    
    for r in records:
        dt = r["dt"]
        if last_dt is not None:
            gap = (dt - last_dt).total_seconds() / 60.0
            if gap > threshold_min and len(current_items) > 0:
                spots.append(current_items)
                current_items = []
        current_items.append(r)
        last_dt = dt
        
    if current_items:
        spots.append(current_items)
        
    print(f"Clustered into {len(spots)} candidate spots (time gap > {threshold_min} min).")
    
    spot_dicts = []
    all_items = []
    total_images = 0
    total_videos = 0
    
    colors = ["#0284c7", "#0d9488", "#f43f5e", "#f59e0b", "#6366f1", "#8b5cf6", "#ec4899", "#10b981"]
    
    for s_idx, sp in enumerate(spots):
        sp_code = letters[s_idx] if s_idx < len(letters) else f"S{s_idx+1}"
        sp_color = colors[s_idx % len(colors)]
        sp_id = f"spot-{s_idx+1:02d}"
        
        d_start = sp[0]["dt"]
        sp_date = d_start.strftime("%Y/%m/%d")
        sp_time = f"{sp[0]['dt'].strftime('%H:%M')}〜{sp[-1]['dt'].strftime('%H:%M')}"
        
        items_json = []
        for i_idx, it in enumerate(sp):
            c_id = f"{sp_code}-{i_idx+1:02d}"
            is_vid = it["type"] == "video"
            if is_vid:
                total_videos += 1
            else:
                total_images += 1
                
            base_name = os.path.splitext(it["filename"])[0]
            item_entry = {
                "id": f"item-{len(all_items)+1:03d}",
                "custom_id": c_id,
                "spot_id": sp_id,
                "spot_code": sp_code,
                "filename": it["filename"],
                "type": it["type"],
                "web_file": f"images/web/{base_name}.jpg" if not is_vid else None,
                "thumb_file": f"images/thumb/{base_name}.jpg" if not is_vid else None,
                "video_file": f"videos/{it['filename']}" if is_vid else None,
                "datetime": it["datetime"],
                "lat": it["lat"],
                "lon": it["lon"],
                "original_path": it["filepath"]
            }
            items_json.append(item_entry)
            all_items.append(item_entry)
            
        spot_dicts.append({
            "id": sp_id,
            "code": sp_code,
            "title": f"スポット {sp_code}",
            "date": sp_date,
            "time": sp_time,
            "color": sp_color,
            "tag": "立ち寄り",
            "badge": "観光",
            "note": "",
            "map_query": f"スポット {sp_code}",
            "items": items_json
        })
        
    album_data = {
        "title": args.title or "トリップアルバム",
        "subtitle": "フォトギャラリー",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_files": len(all_items),
        "total_images": total_images,
        "total_videos": total_videos,
        "spots": spot_dicts,
        "items": all_items
    }
    
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(album_data, f, ensure_ascii=False, indent=2)
        
    print(f"Scan complete! Data saved to: {output_json}")

def cmd_optimize(args):
    """Optimize images and compress videos."""
    data_json = args.data
    base_dir = args.base_dir or "."

    with open(data_json, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    web_dir = os.path.join(base_dir, "images", "web")
    thumb_dir = os.path.join(base_dir, "images", "thumb")
    os.makedirs(web_dir, exist_ok=True)
    os.makedirs(thumb_dir, exist_ok=True)
    
    print("Optimizing images (web: 1600px q80, thumb: 400px q75)...")
    count_img = 0
    for it in data["items"]:
        if it["type"] == "image":
            orig = it["original_path"]
            if not os.path.exists(orig):
                continue
            base = os.path.splitext(it["filename"])[0]
            out_web = os.path.join(web_dir, f"{base}.jpg")
            out_thumb = os.path.join(thumb_dir, f"{base}.jpg")
            
            try:
                with Image.open(orig) as img:
                    img = ImageOps.exif_transpose(img)
                    if img.mode in ("RGBA", "P"):
                        img = img.convert("RGB")
                    
                    if not os.path.exists(out_web):
                        w, h = img.size
                        max_dim = 1600
                        if max(w, h) > max_dim:
                            scale = max_dim / max(w, h)
                            new_size = (int(w * scale), int(h * scale))
                            w_img = img.resize(new_size, Image.Resampling.LANCZOS)
                        else:
                            w_img = img
                        w_img.save(out_web, "JPEG", quality=80, optimize=True)
                        
                    if not os.path.exists(out_thumb):
                        t_img = img.copy()
                        t_img.thumbnail((400, 400), Image.Resampling.LANCZOS)
                        t_img.save(out_thumb, "JPEG", quality=75, optimize=True)
                        
                    count_img += 1
            except Exception as e:
                print(f"Error processing {it['filename']}: {e}", file=sys.stderr)
                
    print(f"Optimized {count_img} images.")

def cmd_qr(args):
    """Generate high quality QR code for album URL."""
    url = args.url
    output_dir = args.output_dir or "."
    os.makedirs(output_dir, exist_ok=True)
    
    import qrcode
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=12,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color='#0f172a', back_color='white')
    
    png_path = os.path.join(output_dir, "qrcode.png")
    img.save(png_path)
    
    img_dir = os.path.join(output_dir, "images")
    if os.path.exists(img_dir):
        shutil.copy(png_path, os.path.join(img_dir, "qrcode.png"))
        
    print(f"QR code generated at {png_path} for {url}")

def main():
    parser = argparse.ArgumentParser(description="Travel Album Generator CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    p_scan = subparsers.add_parser("scan", help="Scan media files and generate album data JSON")
    p_scan.add_argument("--input-dir", required=True, help="Path to input media directory")
    p_scan.add_argument("--output", default="album_data.json", help="Output JSON path")
    p_scan.add_argument("--title", default="トリップアルバム", help="Album title")
    p_scan.add_argument("--cluster-threshold-minutes", type=float, default=30.0, help="Time gap to split spots")
    p_scan.set_defaults(func=cmd_scan)
    
    p_opt = subparsers.add_parser("optimize", help="Optimize images and compress videos")
    p_opt.add_argument("--data", default="album_data.json", help="Path to album_data.json")
    p_opt.add_argument("--base-dir", default=".", help="Base directory")
    p_opt.add_argument("--max-video-mb", type=float, default=2.0, help="Target max size for videos in MB")
    p_opt.set_defaults(func=cmd_optimize)
    
    p_qr = subparsers.add_parser("qr", help="Generate album QR code")
    p_qr.add_argument("--url", required=True, help="Web album public URL")
    p_qr.add_argument("--output-dir", default=".", help="Output directory")
    p_qr.set_defaults(func=cmd_qr)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
