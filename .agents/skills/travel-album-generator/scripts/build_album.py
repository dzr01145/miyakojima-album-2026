import os
import json
import urllib.parse
import math

def build_album(data_path="album_data.json", output_html="index.html", base_dir="."):
    BASE_DIR = os.path.abspath(base_dir)
    DATA_PATH = os.path.abspath(data_path)
    OUTPUT_HTML = os.path.abspath(output_html)
    VIDEOS_DIR = os.path.join(BASE_DIR, "videos")
    WEB_DIR = os.path.join(BASE_DIR, "images", "web")
    THUMB_DIR = os.path.join(BASE_DIR, "images", "thumb")

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Update web and video file sizes in data
    for item in data.get("items", []):
        fn = item["filename"]
        base = os.path.splitext(fn)[0]
        if item["type"] == "video":
            vp = os.path.join(VIDEOS_DIR, fn)
            if os.path.exists(vp):
                item["size_web"] = os.path.getsize(vp)
        else:
            wp = os.path.join(WEB_DIR, f"{base}.jpg")
            if os.path.exists(wp):
                item["size_web"] = os.path.getsize(wp)
            tp = os.path.join(THUMB_DIR, f"{base}.jpg")
            if os.path.exists(tp):
                item["size_thumb"] = os.path.getsize(tp)

    for s in data["spots"]:
        for item in s.get("items", []):
            fn = item["filename"]
            base = os.path.splitext(fn)[0]
            if item["type"] == "video":
                vp = os.path.join(VIDEOS_DIR, fn)
                if os.path.exists(vp):
                    item["size_web"] = os.path.getsize(vp)
            else:
                wp = os.path.join(WEB_DIR, f"{base}.jpg")
                if os.path.exists(wp):
                    item["size_web"] = os.path.getsize(wp)
                tp = os.path.join(THUMB_DIR, f"{base}.jpg")
                if os.path.exists(tp):
                    item["size_thumb"] = os.path.getsize(tp)

    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("Updated album_data.json with accurate file sizes.")

    sidebar_items_html = [
        """          <a href="#routeMapSection" class="sidebar-spot-link map-sidebar-link" id="nav-link-routeMapSection" data-spot-id="routeMapSection" onclick="onSidebarNavClick(event, 'routeMapSection')">
                <span class="nav-badge" style="background: linear-gradient(135deg, #0284c7, #0d9488); font-size: 1.15rem;">🗺️</span>
                <div class="nav-text">
                  <div class="nav-spot-title" style="color: #0284c7; font-weight: 800;">宮古島 全体ルートマップ</div>
                  <div class="nav-spot-meta"><span>📍 A 〜 N の巡り順</span></div>
                </div>
              </a>"""
    ]
    for s in data["spots"]:
        if not s.get("items"):
            continue
        sp_id = s["id"]
        sp_code = s["code"]
        sp_color = s.get("color", "#0284c7")
        sp_title = s["title"]
        sp_date = s["date"]
        sp_time = s["time"]
        sp_count = len(s["items"])
        day_short = sp_date
        
        sidebar_items_html.append(f"""          <a href="#{sp_id}" class="sidebar-spot-link" id="nav-link-{sp_id}" data-spot-id="{sp_id}" onclick="onSidebarNavClick(event, '{sp_id}')">
                <span class="nav-badge" style="background-color: {sp_color};">{sp_code}</span>
                <div class="nav-text">
                  <div class="nav-spot-title">[{sp_code}] {sp_title}</div>
                  <div class="nav-spot-meta"><span>📅 {day_short}</span><span>📷 {sp_count}件</span></div>
                </div>
              </a>""")
    
    sidebar_spots_str = "\n".join(sidebar_items_html)
    
    
    # ==========================================
    # Build Pop Route Map Component Logic
    # ==========================================
    short_names = {
        "spot-01": "さんご家 (会食)",
        "spot-02": "宮古そば まっすぐ",
        "spot-03": "宮古島海中公園",
        "spot-04": "池間大橋＆雪塩",
        "spot-05": "池間島灯台 (最北端)",
        "spot-06": "伊良部大橋",
        "spot-07": "下地島「通り池」",
        "spot-08": "17エンド (下地島空港)",
        "spot-09": "宮古食区 (夜・三線)",
        "spot-10": "久松製麺所 (朝食)",
        "spot-11": "東平安名埼灯台 (絶景)",
        "spot-12": "地下ダム資料館",
        "spot-13": "みなと食堂 (昼食)",
        "spot-14": "A&W 宮古下里店"
    }
    
    MAP_MIN_LON, MAP_MAX_LON = 125.105, 125.495
    MAP_MIN_LAT, MAP_MAX_LAT = 24.690, 24.950
    MAP_VIEW_W, MAP_VIEW_H = 1000, 700
    MAP_PAD_X, MAP_PAD_Y = 60, 60
    
    def map_proj(lon, lat):
        x = MAP_PAD_X + ((lon - MAP_MIN_LON) / (MAP_MAX_LON - MAP_MIN_LON)) * (MAP_VIEW_W - 2 * MAP_PAD_X)
        y = MAP_VIEW_H - MAP_PAD_Y - ((lat - MAP_MIN_LAT) / (MAP_MAX_LAT - MAP_MIN_LAT)) * (MAP_VIEW_H - 2 * MAP_PAD_Y)
        return round(x, 1), round(y, 1)
    
    spots_coords = {}
    for sp_item in data["spots"]:
        lats = [it['lat'] for it in sp_item['items'] if it.get('lat')]
        lons = [it['lon'] for it in sp_item['items'] if it.get('lon')]
        spots_coords[sp_item["id"]] = {
            "lat": sum(lats)/len(lats) if lats else 24.80,
            "lon": sum(lons)/len(lons) if lons else 125.28,
            "code": sp_item["code"],
            "title": sp_item["title"],
            "date": sp_item["date"],
            "color": sp_item.get("color", "#0284c7"),
            "badge": sp_item.get("badge", "")
        }
    
    map_spot_pts = {}
    for sp_id_key, info in spots_coords.items():
        x, y = map_proj(info["lon"], info["lat"])
        code_val = info["code"]
        lbl_dir = "right"
        if code_val in ("A", "I", "N", "M", "J"):
            if code_val == "A": x += 16; y -= 10; lbl_dir = "right"
            elif code_val == "I": x -= 14; y += 14; lbl_dir = "left"
            elif code_val == "M": x += 8; y -= 24; lbl_dir = "top"
            elif code_val == "N": x += 22; y += 22; lbl_dir = "right"
            elif code_val == "J": x -= 16; y += 30; lbl_dir = "left"
        elif code_val == "E": y += 6; lbl_dir = "top"
        elif code_val == "D": x -= 16; lbl_dir = "left"
        elif code_val == "C": x -= 18; lbl_dir = "left"
        elif code_val == "H": x += 10; y -= 6; lbl_dir = "right"
        elif code_val == "G": x += 10; y += 8; lbl_dir = "right"
        elif code_val == "F": x -= 10; y += 20; lbl_dir = "bottom"
        elif code_val == "B": x += 14; y += 18; lbl_dir = "right"
        elif code_val == "K": x += 12; y -= 16; lbl_dir = "top"
        elif code_val == "L": x += 10; y += 20; lbl_dir = "bottom"
        map_spot_pts[sp_id_key] = {
            "x": x, "y": y, "info": info,
            "short_name": short_names.get(sp_id_key, info["title"]),
            "lbl_dir": lbl_dir
        }
    
    mainland_raw = [
        (125.266, 24.915), (125.275, 24.900), (125.282, 24.878), (125.280, 24.845),
        (125.295, 24.825), (125.325, 24.785), (125.352, 24.760), (125.385, 24.745),
        (125.430, 24.733), (125.465, 24.726), (125.478, 24.722), (125.468, 24.714),
        (125.430, 24.717), (125.380, 24.720), (125.335, 24.715), (125.300, 24.715),
        (125.260, 24.718), (125.244, 24.730), (125.250, 24.760), (125.265, 24.785),
        (125.276, 24.810), (125.270, 24.835), (125.250, 24.870), (125.254, 24.902),
        (125.266, 24.915)
    ]
    ikema_raw = [
        (125.234, 24.920), (125.242, 24.938), (125.260, 24.936), (125.268, 24.922),
        (125.256, 24.910), (125.240, 24.912), (125.234, 24.920)
    ]
    irabu_raw = [
        (125.170, 24.862), (125.195, 24.856), (125.220, 24.842), (125.230, 24.820),
        (125.210, 24.802), (125.185, 24.806), (125.166, 24.822), (125.158, 24.845),
        (125.170, 24.862)
    ]
    shimoji_raw = [
        (125.136, 24.848), (125.158, 24.842), (125.162, 24.812), (125.150, 24.792),
        (125.132, 24.810), (125.128, 24.835), (125.136, 24.848)
    ]
    kurima_raw = [
        (125.236, 24.734), (125.252, 24.738), (125.258, 24.718), (125.244, 24.706),
        (125.234, 24.716), (125.236, 24.734)
    ]
    
    def make_map_svg_path(coords):
        pts = [map_proj(lon, lat) for lon, lat in coords]
        d = [f"M {pts[0][0]} {pts[0][1]}"]
        for i in range(len(pts) - 1):
            p1 = pts[i]
            p2 = pts[i+1]
            mx = (p1[0] + p2[0]) / 2
            my = (p1[1] + p2[1]) / 2
            d.append(f"Q {p1[0]} {p1[1]}, {mx} {my}")
        d.append(f"L {pts[-1][0]} {pts[-1][1]} Z")
        return " ".join(d)
    
    path_main = make_map_svg_path(mainland_raw)
    path_ikema = make_map_svg_path(ikema_raw)
    path_irabu = make_map_svg_path(irabu_raw)
    path_shimoji = make_map_svg_path(shimoji_raw)
    path_kurima = make_map_svg_path(kurima_raw)
    
    br_ikema_p1 = map_proj(125.260, 24.908)
    br_ikema_p2 = map_proj(125.252, 24.912)
    br_irabu_p1 = map_proj(125.268, 24.796)
    br_irabu_p2 = map_proj(125.215, 24.815)
    br_kurima_p1 = map_proj(125.255, 24.735)
    br_kurima_p2 = map_proj(125.248, 24.733)
    
    day2_ids = ["spot-01", "spot-02", "spot-03", "spot-04", "spot-05", "spot-06", "spot-07", "spot-08", "spot-09"]
    day3_ids = ["spot-09", "spot-10", "spot-11", "spot-12", "spot-13", "spot-14"]
    
    def make_route_segs(spot_id_list, color_class):
        pts = [(map_spot_pts[sid]["x"], map_spot_pts[sid]["y"]) for sid in spot_id_list]
        svg_elems = []
        for i in range(len(pts) - 1):
            p1 = pts[i]
            p2 = pts[i+1]
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            dist = math.hypot(dx, dy)
            nx = -dy / (dist + 0.001)
            ny = dx / (dist + 0.001)
            curve = min(36.0, dist * 0.15)
            sgn = 1 if (i % 2 == 0) else -1
            cx = (p1[0] + p2[0]) / 2 + nx * curve * sgn
            cy = (p1[1] + p2[1]) / 2 + ny * curve * sgn
            seg_d = f"M {p1[0]} {p1[1]} Q {round(cx, 1)} {round(cy, 1)}, {p2[0]} {p2[1]}"
            t = 0.54
            mx = (1-t)**2 * p1[0] + 2*(1-t)*t * cx + t**2 * p2[0]
            my = (1-t)**2 * p1[1] + 2*(1-t)*t * cy + t**2 * p2[1]
            tang_x = 2*(1-t)*(cx - p1[0]) + 2*t*(p2[0] - cx)
            tang_y = 2*(1-t)*(cy - p1[1]) + 2*t*(p2[1] - cy)
            angle = round(math.degrees(math.atan2(tang_y, tang_x)), 1)
            svg_elems.append(f'<path d="{seg_d}" class="route-line {color_class}" />')
            svg_elems.append(f'<g transform="translate({round(mx,1)}, {round(my,1)}) rotate({angle})" class="route-arrow-marker {color_class}"><polygon points="-6,-5 7,0 -6,5 -2,0" /></g>')
        return "\n          ".join(svg_elems)
    
    day2_routes_svg = make_route_segs(day2_ids, "day2-route")
    day3_routes_svg = make_route_segs(day3_ids, "day3-route")
    
    map_pins_svg = []
    for sp_id_k, data_item in map_spot_pts.items():
        x = data_item["x"]
        y = data_item["y"]
        code_val = data_item["info"]["code"]
        color_val = data_item["info"]["color"]
        name_val = data_item["short_name"]
        day_val = "day-24" if data_item["info"]["date"] == "Day 2" else ("day-25" if data_item["info"]["date"] == "Day 3" else "day-23")
        dir_type = data_item["lbl_dir"]
        char_len = len(name_val)
        box_w = max(90, char_len * 12 + 20)
        box_h = 24
        if dir_type in ("left", "bottom-left"):
            lx = x - box_w - 14; ly = y - box_h / 2
        elif dir_type == "top":
            lx = x - box_w / 2; ly = y - 36
        elif dir_type == "bottom":
            lx = x - box_w / 2; ly = y + 16
        elif dir_type == "top-left":
            lx = x - box_w - 10; ly = y - 28
        else:
            lx = x + 14; ly = y - box_h / 2
        pin_code = f"""
        <g class="map-pin-group" data-spot-id="{sp_id_k}" data-day="{day_val}" onclick="jumpToSpot('{sp_id_k}')">
          <!-- Invisible stable hitbox to prevent cursor flickering -->
          <circle cx="{x}" cy="{y}" r="22" fill="transparent" pointer-events="all" />
          <circle cx="{x}" cy="{y}" r="15" fill="{color_val}" opacity="0.25" class="pin-glow" />
          <circle cx="{x}" cy="{y}" r="11" fill="{color_val}" stroke="#ffffff" stroke-width="2.5" class="pin-core" />
          <text x="{x}" y="{y+4}" text-anchor="middle" font-family="'Plus Jakarta Sans', sans-serif" font-weight="800" font-size="11" fill="#ffffff" pointer-events="none">{code_val}</text>
          <g class="pin-label-bubble">
            <rect x="{lx}" y="{ly}" width="{box_w}" height="{box_h}" rx="6" fill="#ffffff" stroke="{color_val}" stroke-width="1.5" filter="url(#dropShadow)" />
            <text x="{lx + box_w/2}" y="{ly + 16}" text-anchor="middle" font-family="'Zen Kaku Gothic New', sans-serif" font-weight="700" font-size="11" fill="#0f172a" pointer-events="none">[{code_val}] {name_val}</text>
          </g>
        </g>"""
        map_pins_svg.append(pin_code)
    
    map_pins_svg_str = "\n".join(map_pins_svg)
    
    route_map_html = f"""
          <!-- Pop Route Map Section -->
          <section class="route-map-container" id="routeMapSection">
            <div class="map-card-header">
              <div class="map-title-row">
                <div class="map-badge">🗺️ TRIP ROUTE MAP</div>
                <h2>宮古島 旅程ルートマップ</h2>
                <p class="map-sub">3日間のめぐり順（[A] 〜 [N]）を網羅！ピンをクリックすると該当スポットの写真へジャンプします。</p>
              </div>
              <div class="map-filter-row">
                <button class="map-route-btn active" onclick="setMapRouteFilter('all', this)">🌈 すべてのルート</button>
                <button class="map-route-btn day1-btn" onclick="setMapRouteFilter('day-23', this)">📍 Day 1 (平良・会食)</button>
                <button class="map-route-btn day2-btn" onclick="setMapRouteFilter('day-24', this)">🌊 Day 2 (北端・伊良部・下地島)</button>
                <button class="map-route-btn day3-btn" onclick="setMapRouteFilter('day-25', this)">🌺 Day 3 (東平安名崎・市内)</button>
              </div>
            </div>
    
            <div class="svg-map-wrapper">
              <svg viewBox="0 0 {MAP_VIEW_W} {MAP_VIEW_H}" class="pop-map-svg" id="popMapSvg">
                <defs>
                  <linearGradient id="oceanGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#bae6fd" />
                    <stop offset="50%" stop-color="#7dd3fc" />
                    <stop offset="100%" stop-color="#38bdf8" />
                  </linearGradient>
    
                  <linearGradient id="islandGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#fef9c3" />
                    <stop offset="100%" stop-color="#fef08a" />
                  </linearGradient>
    
                  <filter id="dropShadow" x="-20%" y="-20%" width="140%" height="140%">
                    <feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#0f172a" flood-opacity="0.18" />
                  </filter>
                  <filter id="islandShadow" x="-10%" y="-10%" width="120%" height="120%">
                    <feDropShadow dx="0" dy="4" stdDeviation="6" flood-color="#0369a1" flood-opacity="0.25" />
                  </filter>
                </defs>
    
                <!-- Ocean Background -->
                <rect width="{MAP_VIEW_W}" height="{MAP_VIEW_H}" rx="20" fill="url(#oceanGradient)" />
    
                <!-- Waves & Emojis -->
                <g stroke="#ffffff" stroke-width="1.8" fill="none" opacity="0.4" stroke-linecap="round">
                  <path d="M 80 120 Q 95 112, 110 120 T 140 120" />
                  <path d="M 120 135 Q 135 127, 150 135 T 180 135" />
                  <path d="M 780 160 Q 795 152, 810 160 T 840 160" />
                  <path d="M 820 180 Q 835 172, 850 180 T 880 180" />
                  <path d="M 140 560 Q 155 552, 170 560 T 200 560" />
                  <path d="M 460 620 Q 475 612, 490 620 T 520 620" />
                </g>
    
                <text x="80" y="240" font-size="28" opacity="0.85">✈️</text>
                <text x="70" y="265" font-size="11" font-weight="700" fill="#0369a1" font-family="'Zen Kaku Gothic New', sans-serif">下地島空港</text>
                <text x="760" y="280" font-size="28" opacity="0.85">⛵</text>
                <text x="320" y="600" font-size="26" opacity="0.85">🐢</text>
                <text x="860" y="600" font-size="26" opacity="0.85">🐠</text>
                <text x="80" y="80" font-size="28" opacity="0.85">☀️</text>
    
                <!-- Shallow Reef Glow -->
                <g fill="#67e8f9" opacity="0.45" filter="url(#islandShadow)">
                  <path d="{path_main}" transform="scale(1.025) translate(-10, -8)" />
                  <path d="{path_irabu}" transform="scale(1.03) translate(-4, -4)" />
                  <path d="{path_shimoji}" transform="scale(1.03) translate(-4, -4)" />
                  <path d="{path_ikema}" transform="scale(1.04) translate(-4, -4)" />
                  <path d="{path_kurima}" transform="scale(1.04) translate(-4, -4)" />
                </g>
    
                <!-- Islands -->
                <g fill="url(#islandGradient)" stroke="#facc15" stroke-width="2" filter="url(#dropShadow)">
                  <path d="{path_main}" />
                  <path d="{path_irabu}" />
                  <path d="{path_shimoji}" />
                  <path d="{path_ikema}" />
                  <path d="{path_kurima}" />
                </g>
    
                <!-- Bridges -->
                <line x1="{br_ikema_p1[0]}" y1="{br_ikema_p1[1]}" x2="{br_ikema_p2[0]}" y2="{br_ikema_p2[1]}" stroke="#ffffff" stroke-width="5" stroke-linecap="round" />
                <line x1="{br_ikema_p1[0]}" y1="{br_ikema_p1[1]}" x2="{br_ikema_p2[0]}" y2="{br_ikema_p2[1]}" stroke="#0284c7" stroke-width="3" stroke-dasharray="2 3" stroke-linecap="round" />
                <text x="{(br_ikema_p1[0]+br_ikema_p2[0])/2 + 10}" y="{(br_ikema_p1[1]+br_ikema_p2[1])/2 + 4}" font-size="10" font-weight="700" fill="#0369a1" font-family="'Zen Kaku Gothic New', sans-serif">池間大橋</text>
    
                <line x1="{br_irabu_p1[0]}" y1="{br_irabu_p1[1]}" x2="{br_irabu_p2[0]}" y2="{br_irabu_p2[1]}" stroke="#ffffff" stroke-width="5" stroke-linecap="round" />
                <line x1="{br_irabu_p1[0]}" y1="{br_irabu_p1[1]}" x2="{br_irabu_p2[0]}" y2="{br_irabu_p2[1]}" stroke="#0284c7" stroke-width="3" stroke-dasharray="3 3" stroke-linecap="round" />
                <text x="{(br_irabu_p1[0]+br_irabu_p2[0])/2 - 14}" y="{(br_irabu_p1[1]+br_irabu_p2[1])/2 - 8}" font-size="10" font-weight="700" fill="#0369a1" font-family="'Zen Kaku Gothic New', sans-serif">伊良部大橋 (3,540m)</text>
    
                <line x1="{br_kurima_p1[0]}" y1="{br_kurima_p1[1]}" x2="{br_kurima_p2[0]}" y2="{br_kurima_p2[1]}" stroke="#ffffff" stroke-width="4" stroke-linecap="round" />
                <line x1="{br_kurima_p1[0]}" y1="{br_kurima_p1[1]}" x2="{br_kurima_p2[0]}" y2="{br_kurima_p2[1]}" stroke="#0284c7" stroke-width="2" stroke-dasharray="2 2" stroke-linecap="round" />
                <text x="{(br_kurima_p1[0]+br_kurima_p2[0])/2 + 8}" y="{(br_kurima_p1[1]+br_kurima_p2[1])/2 + 12}" font-size="9" font-weight="700" fill="#0369a1" font-family="'Zen Kaku Gothic New', sans-serif">来間大橋</text>
    
                <!-- Island Names Watermark -->
                <text x="560" y="440" font-size="24" font-weight="800" fill="#ca8a04" opacity="0.35" font-family="'Plus Jakarta Sans', sans-serif" letter-spacing="4">宮古島</text>
                <text x="180" y="320" font-size="14" font-weight="800" fill="#ca8a04" opacity="0.4" font-family="'Plus Jakarta Sans', sans-serif">伊良部島</text>
                <text x="130" y="370" font-size="13" font-weight="800" fill="#ca8a04" opacity="0.4" font-family="'Plus Jakarta Sans', sans-serif">下地島</text>
                <text x="310" y="86" font-size="13" font-weight="800" fill="#ca8a04" opacity="0.4" font-family="'Plus Jakarta Sans', sans-serif">池間島</text>
                <text x="280" y="590" font-size="12" font-weight="800" fill="#ca8a04" opacity="0.4" font-family="'Plus Jakarta Sans', sans-serif">来間島</text>
    
                <!-- Route Lines -->
                <g class="route-layer day2-layer" id="day2RouteLayer">
                  {day2_routes_svg}
                </g>
                <g class="route-layer day3-layer" id="day3RouteLayer">
                  {day3_routes_svg}
                </g>
    
                <!-- Pins & Bubbles -->
                <g class="pins-layer" id="pinsLayer">
                  {map_pins_svg_str}
                </g>
              </svg>
            </div>
          </section>
    """
    
    # 2. Build Sections HTML
    sections_html = []
    for s in data["spots"]:
        sp_id = s["id"]
        sp_code = s["code"]
        sp_color = s.get("color", "#0284c7")
        sp_tag = s.get("tag", "立ち寄り")
        sp_date = s["date"]
        sp_time = s["time"]
        sp_title = s["title"]
        sp_note = s["note"]
        is_memo = s.get("is_memo", False)
        items = s.get("items", [])
        if not items:
            continue
            
        has_video = any(x["type"] == "video" for x in items)
        has_burst = any(x.get("is_burst", False) for x in items)
        category = s.get("category", "sightseeing")
        
        day_class = "day-24" if ("04/24" in sp_date or "Day 2" in sp_date) else ("day-25" if ("04/25" in sp_date or "Day 3" in sp_date) else "day-23")
        
        # Construct optimal map link
        if sp_id == "spot-01":
            map_link = 'https://www.google.com/maps/search/?api=1&query=' + urllib.parse.quote('居酒屋 さんご家 宮古島')
            map_btn_html = f'<a href="{map_link}" target="_blank" rel="noopener" class="map-btn" title="Google Mapsで「居酒屋 さんご家」を開く">📍 居酒屋 さんご家 の地図</a>'
        elif sp_id == "spot-12":
            dam_link = 'https://risem.net/8995/'
            map_btn_html = f'<a href="{dam_link}" target="_blank" rel="noopener" class="map-btn" style="background:#f0f9ff;border-color:#0284c7;color:#0284c7;" title="施設写真・詳細案内を見る">🏛️ 施設写真・案内（リンク先）</a>'
        else:
            map_q = s.get("map_query", sp_title)
            encoded_q = urllib.parse.quote(map_q)
            map_link = f'https://www.google.com/maps/search/?api=1&query={encoded_q}'
            map_btn_html = f'<a href="{map_link}" target="_blank" rel="noopener" class="map-btn" title="Google Mapsで店舗・スポットを開く">📍 {map_q.split()[0]} の地図</a>'
        
        quote_class = 'memo-quote' if is_memo else ''
        quote_icon = '📝' if is_memo else '🍜' if 'そば' in sp_title else '🍽️' if category == 'gourmet' else '🌴'
        quote_label = '旅程メモより' if is_memo else 'スポット情報'
    
        sp_note_html = sp_note
        if sp_id == "spot-12":
            dam_link = 'https://risem.net/8995/'
            sp_note_html = f'宮古島市地下ダム資料館 よくメカニズムわかりました。300円は安いです（中の写真は撮影禁止のため、館内の展示内容や写真等は <a href="{dam_link}" target="_blank" rel="noopener" style="color:#0284c7;font-weight:700;text-decoration:underline;">こちら（リンク先：施設写真・案内）</a> をご参照ください）'
    
        sec_head = f"""
        <!-- Spot: {sp_title} -->
        <section class="spot-section" id="{sp_id}" data-category="{category}" data-day="{day_class}" data-has-video="{'true' if has_video else 'false'}" data-has-burst="{'true' if has_burst else 'false'}">
          <div class="spot-header">
            <div class="spot-header-left">
              <div class="spot-code-badge" style="background-color: {sp_color};">{sp_code}</div>
              <div class="spot-title-area">
                <h2>[{sp_code}] {sp_title} <span class="spot-tag-badge" style="background-color: {sp_color};">{sp_tag}</span></h2>
                <div class="spot-meta">
                  <span>📅 {sp_date}</span>
                  <span>📷 ID: {items[0]['custom_id']} 〜 {items[-1]['custom_id']} ({len(items)}件)</span>
                </div>
              </div>
            </div>
            <div class="spot-header-right">
              {map_btn_html}
            </div>
          </div>
    
          <!-- User Travel Memo -->
          <div class="spot-note-box {quote_class}">
            <div class="note-icon">{quote_icon}</div>
            <div>
              <div class="note-label">{quote_label}</div>
              <div class="note-content">{sp_note_html}</div>
            </div>
          </div>
    
          <!-- Media Grid -->
          <div class="media-grid">
    """
        cards_html = []
        for item in items:
            it_id = item["id"]
            it_custom_id = item["custom_id"]
            it_type = item["type"]
            it_dt = item.get("datetime", "")
            it_time_str = it_dt.split()[1] if ' ' in it_dt else ''
            it_fn = item["filename"]
            it_burst = item.get("is_burst", False)
            burst_badge = '<div class="burst-badge" title="前後の写真と連続して撮影されています">👯 連続・類似</div>' if it_burst else ''
            burst_data = 'true' if it_burst else 'false'
    
            if it_type == "image":
                thumb = item.get("thumb_file", "")
                card = f"""        <div class="photo-item-card" id="card-{it_id}" data-item-id="{it_id}" data-custom-id="{it_custom_id}" data-filename="{it_fn}" data-burst="{burst_data}">
              <div class="delete-strike-overlay">🗑️ 削除候補</div>
              {burst_badge}
              <div class="photo-thumb-wrap" onclick="openLightbox('{it_id}')">
                <img src="{thumb}" alt="{it_fn}" loading="lazy">
              </div>
              <div class="card-footer-info">
                <div class="card-id-row">
                  <span class="photo-id-tag">{it_custom_id}</span>
                </div>
                <div class="delete-action-row">
                  <label class="delete-check-label">
                    <input type="checkbox" class="delete-checkbox" data-item-id="{it_id}" onchange="toggleItemDelete('{it_id}', this.checked)">
                    <span>削除候補にする</span>
                  </label>
                  <button class="zoom-btn-small" onclick="openLightbox('{it_id}')">🔍 拡大</button>
                </div>
              </div>
            </div>"""
            else:
                v_size_mb = item.get("size_web", 0) / (1024 * 1024)
                card = f"""        <div class="photo-item-card" id="card-{it_id}" data-item-id="{it_id}" data-custom-id="{it_custom_id}" data-filename="{it_fn}" data-burst="false">
              <div class="delete-strike-overlay">🗑️ 削除候補</div>
              <div class="photo-thumb-wrap video-wrap" onclick="openLightbox('{it_id}')">
                <div class="video-play-btn">
                  <div class="play-circle">▶</div>
                </div>
              </div>
              <div class="card-footer-info">
                <div class="card-id-row">
                  <span class="photo-id-tag" style="background-color: #6366f1;">{it_custom_id} [動画]</span>
                  <span class="photo-time-label" style="background:#e0e7ff;color:#4338ca;">🎬 {v_size_mb:.2f}MB</span>
                </div>
                <div class="delete-action-row">
                  <label class="delete-check-label">
                    <input type="checkbox" class="delete-checkbox" data-item-id="{it_id}" onchange="toggleItemDelete('{it_id}', this.checked)">
                    <span>削除候補にする</span>
                  </label>
                  <button class="zoom-btn-small" onclick="openLightbox('{it_id}')">▶ 再生</button>
                </div>
              </div>
            </div>"""
            cards_html.append(card)
    
        sec_foot = """      </div>
        </section>"""
        sections_html.append(sec_head + "\n".join(cards_html) + "\n" + sec_foot)
    
    all_sections_str = "\n".join(sections_html)
    json_items_str = json.dumps(data["items"], ensure_ascii=False)
    json_spots_str = json.dumps(data["spots"], ensure_ascii=False)
    
    # HTML Template with Left Sidebar Navigation & Easily Restorable Delete Mode
    html_template = """<!DOCTYPE html>
    <html lang="ja">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>宮古島 トリップアルバム 2026 | 青い海と絶景の旅程記録</title>
      <link rel="preconnect" href="https://fonts.googleapis.com">
      <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
      <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&family=Zen+Kaku+Gothic+New:wght@400;500;700&display=swap" rel="stylesheet">
      <style>
        :root {
          --primary: #0284c7;
          --primary-dark: #0369a1;
          --primary-light: #e0f2fe;
          --accent: #0d9488;
          --coral: #f43f5e;
          --amber: #f59e0b;
          --bg-main: #f8fafc;
          --bg-card: #ffffff;
          --text-main: #0f172a;
          --text-muted: #64748b;
          --border: #e2e8f0;
          --sidebar-width: 320px;
          --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
          --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.07), 0 2px 4px -2px rgb(0 0 0 / 0.07);
          --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.08), 0 4px 6px -4px rgb(0 0 0 / 0.08);
          --shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1);
          --radius-lg: 16px;
          --radius-md: 10px;
        }
    
        * {
          box-sizing: border-box;
          margin: 0;
          padding: 0;
        }
    
        html {
          scroll-behavior: smooth;
        }
    
        body {
          font-family: 'Zen Kaku Gothic New', 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
          background-color: var(--bg-main);
          color: var(--text-main);
          line-height: 1.6;
          -webkit-font-smoothing: antialiased;
        }
    
        /* Layout Wrapper */
        .app-layout {
          display: flex;
          min-height: 100vh;
          position: relative;
        }
    
        /* Left Sidebar Navigation */
        .sidebar {
          width: var(--sidebar-width);
          height: 100vh;
          position: sticky;
          top: 0;
          background: #ffffff;
          border-right: 1px solid var(--border);
          display: flex;
          flex-direction: column;
          flex-shrink: 0;
          z-index: 900;
          box-shadow: 2px 0 10px rgba(0,0,0,0.03);
        }
    
        .sidebar-header {
          padding: 24px 20px 16px;
          border-bottom: 1px solid var(--border);
          background: #fafbfc;
          display: flex;
          align-items: center;
          justify-content: space-between;
        }
    
        .sidebar-title-area {
          display: flex;
          flex-direction: column;
          cursor: pointer;
          user-select: none;
          padding: 6px 10px;
          margin: -6px -10px;
          border-radius: 10px;
          transition: background 0.2s ease, transform 0.15s ease, opacity 0.2s ease;
        }
    
        .sidebar-title-area:hover {
          background: #e2e8f0;
          opacity: 0.9;
        }
    
        .sidebar-title-area:active {
          transform: scale(0.98);
        }
    
        .sidebar-brand {
          font-size: 1.15rem;
          font-weight: 800;
          color: var(--primary-dark);
          display: flex;
          align-items: center;
          gap: 8px;
          letter-spacing: -0.01em;
        }
    
        .sidebar-sub {
          font-size: 0.75rem;
          color: var(--text-muted);
          margin-top: 2px;
          font-weight: 500;
        }
    
        .sidebar-close-btn {
          display: none;
          background: transparent;
          border: none;
          font-size: 1.4rem;
          color: var(--text-muted);
          cursor: pointer;
          padding: 4px 8px;
          border-radius: 6px;
        }
    
        .sidebar-close-btn:hover {
          background: #f1f5f9;
          color: var(--text-main);
        }
    
        /* Sidebar Filters Section */
        .sidebar-filters-box {
          padding: 14px 16px;
          border-bottom: 1px solid var(--border);
          background: #ffffff;
        }
    
        .sidebar-section-label {
          font-size: 0.72rem;
          font-weight: 700;
          color: var(--text-muted);
          text-transform: uppercase;
          letter-spacing: 0.05em;
          margin-bottom: 8px;
        }
    
        .filter-pills-row {
          display: flex;
          flex-wrap: wrap;
          gap: 6px;
        }
    
        .filter-btn {
          background: #f1f5f9;
          border: 1px solid var(--border);
          padding: 5px 11px;
          border-radius: 999px;
          font-size: 0.78rem;
          font-weight: 600;
          color: var(--text-muted);
          cursor: pointer;
          white-space: nowrap;
          transition: all 0.2s;
        }
    
        .filter-btn:hover {
          background: #e2e8f0;
          color: var(--text-main);
        }
    
        .filter-btn.active {
          background: var(--primary);
          color: white;
          border-color: var(--primary);
        }
    
        /* Sidebar Spot Nav List */
        .sidebar-nav-container {
          flex: 1;
          overflow-y: auto;
          padding: 12px 10px 24px;
          scrollbar-width: thin;
        }
    
        .sidebar-nav-container::-webkit-scrollbar {
          width: 5px;
        }
        .sidebar-nav-container::-webkit-scrollbar-thumb {
          background: #cbd5e1;
          border-radius: 4px;
        }
    
        .sidebar-spot-link {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 9px 12px;
          border-radius: var(--radius-md);
          text-decoration: none;
          color: var(--text-main);
          margin-bottom: 4px;
          transition: all 0.15s ease;
          border-left: 3px solid transparent;
        }
    
        .sidebar-spot-link:hover {
          background: #f1f5f9;
        }
    
        .sidebar-spot-link.active {
          background: #e0f2fe;
          border-left-color: var(--primary);
        }
    
        .sidebar-spot-link.active .nav-spot-title {
          color: var(--primary-dark);
          font-weight: 700;
        }
    
        .nav-badge {
          width: 30px;
          height: 30px;
          border-radius: 8px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: 800;
          font-size: 0.95rem;
          color: white;
          flex-shrink: 0;
          font-family: 'Plus Jakarta Sans', sans-serif;
        }
    
        .nav-text {
          flex: 1;
          min-width: 0;
        }
    
        .nav-spot-title {
          font-size: 0.85rem;
          font-weight: 600;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
          color: #1e293b;
        }
    
        .nav-spot-meta {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 6px;
          font-size: 0.72rem;
          color: var(--text-muted);
          margin-top: 2px;
        }
    
        /* Main Content Area */
        .main-body {
          flex: 1;
          min-width: 0;
          display: flex;
          flex-direction: column;
        }
    
        /* Mobile Top Bar */
        .mobile-top-bar {
          display: none;
          position: sticky;
          top: 0;
          z-index: 800;
          background: rgba(255, 255, 255, 0.96);
          backdrop-filter: blur(12px);
          border-bottom: 1px solid var(--border);
          padding: 10px 16px;
          align-items: center;
          justify-content: space-between;
          box-shadow: var(--shadow-sm);
        }
    
        .mobile-menu-btn {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 6px 14px;
          background: var(--primary);
          color: white;
          border: none;
          border-radius: 8px;
          font-size: 0.85rem;
          font-weight: 700;
          cursor: pointer;
        }
    
        .mobile-brand-title {
          font-size: 0.95rem;
          font-weight: 800;
          color: var(--text-main);
          cursor: pointer;
          user-select: none;
          padding: 4px 8px;
          border-radius: 6px;
          transition: opacity 0.2s;
        }
    
        .mobile-brand-title:hover {
          opacity: 0.75;
        }
    
        /* Mobile Drawer Backdrop */
        .sidebar-backdrop {
          display: none;
          position: fixed;
          inset: 0;
          background: rgba(15, 23, 42, 0.4);
          backdrop-filter: blur(4px);
          z-index: 890;
        }
    
        /* Hero Header */
        .hero {
          position: relative;
          background: linear-gradient(135deg, #0369a1 0%, #0284c7 40%, #0d9488 100%);
          color: white;
          padding: 50px 24px 60px;
          text-align: center;
          overflow: hidden;
        }
    
        .hero::before {
          content: "";
          position: absolute;
          top: -50%;
          left: -50%;
          width: 200%;
          height: 200%;
          background: radial-gradient(circle, rgba(255,255,255,0.12) 0%, transparent 60%);
          pointer-events: none;
        }
    
        .hero-inner {
          position: relative;
          max-width: 850px;
          margin: 0 auto;
        }
    
        .hero-badge {
          display: inline-flex;
          align-items: center;
          gap: 8px;
          padding: 5px 14px;
          background: rgba(255, 255, 255, 0.2);
          backdrop-filter: blur(10px);
          border-radius: 999px;
          font-size: 0.825rem;
          font-weight: 600;
          letter-spacing: 0.05em;
          margin-bottom: 16px;
          border: 1px solid rgba(255, 255, 255, 0.3);
        }
    
        .hero h1 {
          font-size: clamp(1.8rem, 4vw, 2.8rem);
          font-weight: 800;
          letter-spacing: -0.02em;
          line-height: 1.25;
          margin-bottom: 12px;
          text-shadow: 0 2px 10px rgba(0,0,0,0.15);
        }
    
        .hero p.lead {
          font-size: clamp(0.95rem, 2vw, 1.15rem);
          opacity: 0.95;
          font-weight: 400;
          max-width: 650px;
          margin: 0 auto 24px;
        }
    
        .stats-bar {
          display: flex;
          flex-wrap: wrap;
          justify-content: center;
          gap: 12px;
          max-width: 750px;
          margin: 0 auto;
        }
    
        .stat-box {
          background: rgba(255, 255, 255, 0.15);
          backdrop-filter: blur(8px);
          border: 1px solid rgba(255, 255, 255, 0.25);
          border-radius: var(--radius-md);
          padding: 10px 16px;
          min-width: 120px;
        }
    
        .stat-num {
          font-size: 1.45rem;
          font-weight: 800;
          font-family: 'Plus Jakarta Sans', sans-serif;
        }
    
        .stat-lbl {
          font-size: 0.72rem;
          opacity: 0.85;
          font-weight: 500;
        }
    
    
        /* Small QR Trigger Button (Top Left of Hero Header) */
        .hero-qr-trigger-btn {
          position: absolute;
          top: 18px;
          left: 22px;
          z-index: 20;
          display: inline-flex;
          align-items: center;
          gap: 7px;
          background: rgba(255, 255, 255, 0.2);
          backdrop-filter: blur(10px);
          -webkit-backdrop-filter: blur(10px);
          border: 1px solid rgba(255, 255, 255, 0.38);
          color: #ffffff;
          padding: 6px 14px;
          border-radius: 999px;
          font-size: 0.8rem;
          font-weight: 700;
          cursor: pointer;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
          transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
        }
    
        .hero-qr-trigger-btn:hover {
          background: rgba(255, 255, 255, 0.35);
          transform: translateY(-1px);
          box-shadow: 0 6px 16px rgba(0, 0, 0, 0.18);
        }
    
        .hero-qr-trigger-btn:active {
          transform: scale(0.97);
        }
    
        .qr-trigger-icon {
          width: 18px;
          height: 18px;
          border-radius: 4px;
          background: #ffffff;
          padding: 2px;
          object-fit: contain;
          flex-shrink: 0;
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
        }
    
        /* Mobile QR Button in Top Bar */
        .mobile-qr-btn {
          display: inline-flex;
          align-items: center;
          gap: 5px;
          padding: 5px 10px;
          background: rgba(2, 132, 199, 0.12);
          border: 1px solid #bae6fd;
          color: var(--primary-dark);
          border-radius: 8px;
          font-size: 0.78rem;
          font-weight: 700;
          cursor: pointer;
          transition: all 0.2s;
        }
    
        .mobile-qr-btn:hover {
          background: #e0f2fe;
        }
    
        .mobile-qr-btn .qr-trigger-icon {
          width: 16px;
          height: 16px;
          padding: 1px;
        }
    
        @media (max-width: 640px) {
          .hero-qr-trigger-btn {
            display: none;
          }
        }
    
        /* QR Modal */
        .qr-modal-overlay {
          display: none;
          position: fixed;
          inset: 0;
          z-index: 1050;
          background: rgba(15, 23, 42, 0.78);
          backdrop-filter: blur(10px);
          -webkit-backdrop-filter: blur(10px);
          align-items: center;
          justify-content: center;
          padding: 20px;
        }
    
        .qr-modal-overlay.active {
          display: flex;
          animation: qrFadeIn 0.2s ease-out;
        }
    
        @keyframes qrFadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
    
        .qr-modal-dialog {
          background: #ffffff;
          border-radius: 20px;
          padding: 28px 24px;
          max-width: 360px;
          width: 100%;
          text-align: center;
          position: relative;
          box-shadow: 0 24px 48px -12px rgba(0, 0, 0, 0.28);
          animation: qrSlideUp 0.25s cubic-bezier(0.16, 1, 0.3, 1);
        }
    
        @keyframes qrSlideUp {
          from { transform: translateY(20px) scale(0.96); opacity: 0; }
          to { transform: translateY(0) scale(1); opacity: 1; }
        }
    
        .qr-modal-close-btn {
          position: absolute;
          top: 14px;
          right: 14px;
          background: #f1f5f9;
          border: none;
          width: 32px;
          height: 32px;
          border-radius: 50%;
          font-size: 1rem;
          color: #64748b;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: all 0.2s;
        }
    
        .qr-modal-close-btn:hover {
          background: #e2e8f0;
          color: #0f172a;
        }
    
        .qr-modal-pill {
          display: inline-block;
          background: #e0f2fe;
          color: #0284c7;
          font-size: 0.72rem;
          font-weight: 800;
          padding: 3px 12px;
          border-radius: 999px;
          margin-bottom: 10px;
          letter-spacing: 0.04em;
        }
    
        .qr-modal-heading {
          font-size: 1.15rem;
          font-weight: 800;
          color: #0f172a;
          margin-bottom: 4px;
        }
    
        .qr-modal-subtitle {
          font-size: 0.8rem;
          color: #64748b;
          margin-bottom: 16px;
        }
    
        .qr-modal-frame {
          display: inline-block;
          background: #f8fafc;
          padding: 12px;
          border-radius: 16px;
          border: 1px solid #e2e8f0;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
          margin-bottom: 18px;
        }
    
        .qr-modal-large-img {
          display: block;
          width: 210px;
          height: 210px;
          border-radius: 8px;
        }
    
        .qr-modal-action-close {
          background: #f1f5f9;
          color: #475569;
          border: 1px solid #cbd5e1;
          padding: 8px 26px;
          border-radius: 999px;
          font-size: 0.85rem;
          font-weight: 700;
          cursor: pointer;
          transition: all 0.2s;
        }
    
        .qr-modal-action-close:hover {
          background: #e2e8f0;
          color: #0f172a;
        }
          .hero-qr-badges,
          .hero-qr-buttons {
            justify-content: center;
          }
        }
    
    
        /* Pop Route Map Section */
        .route-map-container {
          background: #ffffff;
          border-radius: var(--radius-lg);
          border: 1px solid var(--border);
          box-shadow: var(--shadow-md);
          margin: 0 auto 36px;
          overflow: hidden;
          width: 100%;
        }
    
        .map-card-header {
          padding: 24px 28px 18px;
          border-bottom: 1px solid var(--border);
          background: #fafbfc;
          display: flex;
          justify-content: space-between;
          align-items: center;
          flex-wrap: wrap;
          gap: 16px;
        }
    
        .map-title-row {
          max-width: 600px;
        }
    
        .map-badge {
          display: inline-block;
          font-size: 0.72rem;
          font-weight: 800;
          letter-spacing: 0.06em;
          color: #0284c7;
          background: #e0f2fe;
          padding: 3px 10px;
          border-radius: 999px;
          margin-bottom: 6px;
        }
    
        .map-title-row h2 {
          font-size: 1.35rem;
          font-weight: 800;
          color: var(--text-main);
          letter-spacing: -0.01em;
          line-height: 1.3;
        }
    
        .map-sub {
          font-size: 0.82rem;
          color: var(--text-muted);
          margin-top: 4px;
        }
    
        .map-filter-row {
          display: flex;
          gap: 8px;
          flex-wrap: wrap;
        }
    
        .map-route-btn {
          padding: 7px 14px;
          border-radius: 999px;
          border: 1px solid var(--border);
          background: #ffffff;
          color: var(--text-muted);
          font-size: 0.8rem;
          font-weight: 700;
          cursor: pointer;
          transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
          display: inline-flex;
          align-items: center;
          gap: 6px;
        }
    
        .map-route-btn:hover {
          background: #f1f5f9;
          color: var(--text-main);
          transform: translateY(-1px);
        }
    
        .map-route-btn.active {
          background: #0284c7;
          color: #ffffff;
          border-color: #0284c7;
          box-shadow: 0 4px 10px rgba(2, 132, 199, 0.3);
        }
    
        .map-route-btn.day1-btn.active {
          background: #e11d48;
          border-color: #e11d48;
          box-shadow: 0 4px 10px rgba(225, 29, 72, 0.3);
        }
    
        .map-route-btn.day2-btn.active {
          background: #0d9488;
          border-color: #0d9488;
          box-shadow: 0 4px 10px rgba(13, 148, 136, 0.3);
        }
    
        .map-route-btn.day3-btn.active {
          background: #f59e0b;
          border-color: #f59e0b;
          box-shadow: 0 4px 10px rgba(245, 158, 11, 0.3);
        }
    
        .svg-map-wrapper {
          padding: 16px 20px 24px;
          background: #f0f9ff;
          display: flex;
          justify-content: center;
          overflow-x: auto;
        }
    
        .pop-map-svg {
          width: 100%;
          max-width: 1050px;
          height: auto;
          display: block;
          border-radius: 16px;
          box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
          user-select: none;
        }
    
        /* Route Lines & Animation */
        .route-line {
          fill: none;
          stroke-linecap: round;
          stroke-linejoin: round;
          transition: opacity 0.3s ease;
        }
    
        .route-line.day2-route {
          stroke: #0284c7;
          stroke-width: 3.5;
          stroke-dasharray: 8 6;
          animation: dashFlow 25s linear infinite;
        }
    
        .route-line.day3-route {
          stroke: #f97316;
          stroke-width: 3.5;
          stroke-dasharray: 8 6;
          animation: dashFlow 25s linear infinite;
        }
    
        @keyframes dashFlow {
          to {
            stroke-dashoffset: -1000;
          }
        }
    
        .route-arrow-marker polygon {
          transition: opacity 0.3s ease;
        }
    
        .route-arrow-marker.day2-route polygon {
          fill: #0284c7;
        }
    
        .route-arrow-marker.day3-route polygon {
          fill: #f97316;
        }
    
        /* Pin Styles & Pop Interactivity (No Jitter) */
        .map-pin-group {
          cursor: pointer;
          user-select: none;
        }
    
        .map-pin-group .pin-core {
          transition: stroke 0.2s ease, stroke-width 0.2s ease, fill 0.2s ease;
        }
    
        .map-pin-group .pin-label-bubble rect {
          transition: fill 0.2s ease, stroke 0.2s ease, stroke-width 0.2s ease;
        }
    
        .map-pin-group .pin-label-bubble text {
          transition: fill 0.2s ease;
        }
    
        .map-pin-group:hover .pin-core {
          stroke: #facc15;
          stroke-width: 4px;
        }
    
        .map-pin-group:hover .pin-glow {
          opacity: 0.65;
          fill: #facc15;
        }
    
        .map-pin-group:hover .pin-label-bubble rect {
          fill: #0f172a;
          stroke: #38bdf8;
          stroke-width: 2.2px;
        }
    
        .map-pin-group:hover .pin-label-bubble text {
          fill: #ffffff;
          font-weight: 800;
        }
    
        .pin-glow {
          animation: pulseGlow 2.5s infinite ease-in-out;
          pointer-events: none;
        }
    
        @keyframes pulseGlow {
          0%, 100% { opacity: 0.2; }
          50% { opacity: 0.55; }
        }
    
        /* Floating Jump to Map Button */
        .floating-map-btn {
          position: fixed;
          bottom: 28px;
          right: 28px;
          z-index: 980;
          display: flex;
          align-items: center;
          gap: 8px;
          background: linear-gradient(135deg, #0284c7 0%, #0d9488 100%);
          color: #ffffff;
          padding: 11px 20px;
          border-radius: 999px;
          box-shadow: 0 8px 24px rgba(2, 132, 199, 0.45), 0 2px 6px rgba(0, 0, 0, 0.15);
          border: 2px solid rgba(255, 255, 255, 0.45);
          font-size: 0.88rem;
          font-weight: 800;
          cursor: pointer;
          text-decoration: none;
          transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
          opacity: 0;
          visibility: hidden;
          transform: translateY(20px);
        }
    
        .floating-map-btn.visible {
          opacity: 1;
          visibility: visible;
          transform: translateY(0);
        }
    
        .floating-map-btn:hover {
          transform: translateY(-3px) scale(1.04);
          box-shadow: 0 12px 28px rgba(2, 132, 199, 0.55), 0 4px 10px rgba(0, 0, 0, 0.2);
          color: #ffffff;
        }
    
        .floating-map-icon {
          font-size: 1.15rem;
        }
    
        /* Sidebar Map Link Style */
        .map-sidebar-link {
          background: #f0f9ff;
          border: 1px solid #bae6fd;
          margin-bottom: 8px;
        }
    
        .map-sidebar-link:hover {
          background: #e0f2fe;
        }
    
        .dimmed {
          opacity: 0.12 !important;
          pointer-events: none;
        }
    
        /* Main Container */
        .main-content {
          max-width: 1250px;
          margin: 32px auto;
          padding: 0 24px;
          width: 100%;
        }
    
        /* Spot Section */
        .spot-section {
          background: var(--bg-card);
          border-radius: var(--radius-lg);
          border: 1px solid var(--border);
          box-shadow: var(--shadow-md);
          margin-bottom: 40px;
          overflow: hidden;
          transition: box-shadow 0.3s;
          scroll-margin-top: 20px;
        }
    
        .spot-section:hover {
          box-shadow: var(--shadow-lg);
        }
    
        .spot-header {
          padding: 20px 28px;
          border-bottom: 1px solid var(--border);
          background: #fafbfc;
          display: flex;
          flex-wrap: wrap;
          align-items: center;
          justify-content: space-between;
          gap: 14px;
        }
    
        .spot-header-left {
          display: flex;
          align-items: center;
          gap: 14px;
          flex-wrap: wrap;
        }
    
        .spot-code-badge {
          width: 44px;
          height: 44px;
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: 800;
          font-size: 1.25rem;
          color: white;
          flex-shrink: 0;
          font-family: 'Plus Jakarta Sans', sans-serif;
          box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        }
    
        .spot-title-area h2 {
          font-size: 1.25rem;
          font-weight: 700;
          color: var(--text-main);
          display: flex;
          align-items: center;
          gap: 10px;
          flex-wrap: wrap;
        }
    
        .spot-tag-badge {
          font-size: 0.75rem;
          padding: 3px 10px;
          border-radius: 999px;
          font-weight: 600;
          color: white;
        }
    
        .spot-meta {
          display: flex;
          align-items: center;
          gap: 12px;
          font-size: 0.825rem;
          color: var(--text-muted);
          margin-top: 3px;
        }
    
        .map-btn {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 6px 14px;
          background: white;
          border: 1px solid #cbd5e1;
          border-radius: var(--radius-md);
          font-size: 0.825rem;
          font-weight: 600;
          color: #334155;
          text-decoration: none;
          transition: all 0.2s;
        }
    
        .map-btn:hover {
          background: #f1f5f9;
          border-color: #0284c7;
          color: #0284c7;
        }
    
        /* Note Box */
        .spot-note-box {
          padding: 16px 28px;
          background: linear-gradient(to right, #f0fdf4, #f8fafc);
          border-bottom: 1px solid var(--border);
          display: flex;
          align-items: flex-start;
          gap: 14px;
        }
    
        .spot-note-box.memo-quote {
          background: linear-gradient(to right, #f0f9ff, #f8fafc);
          border-left: 4px solid var(--primary);
        }
    
        .note-icon {
          font-size: 1.25rem;
          line-height: 1;
          margin-top: 2px;
        }
    
        .note-content {
          font-size: 0.95rem;
          color: #1e293b;
          line-height: 1.6;
        }
    
        .note-label {
          font-size: 0.72rem;
          font-weight: 700;
          color: var(--primary-dark);
          text-transform: uppercase;
          letter-spacing: 0.05em;
          margin-bottom: 2px;
        }
    
        /* Media Grid */
        .media-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
          gap: 18px;
          padding: 22px 28px 28px;
        }
    
        /* Item Card */
        .photo-item-card {
          background: #ffffff;
          border: 1px solid var(--border);
          border-radius: var(--radius-md);
          overflow: hidden;
          box-shadow: var(--shadow-sm);
          transition: transform 0.2s, box-shadow 0.2s, border-color 0.2s;
          display: flex;
          flex-direction: column;
          position: relative;
        }
    
        .photo-item-card:hover {
          transform: translateY(-3px);
          box-shadow: var(--shadow-lg);
          border-color: #cbd5e1;
        }
    
        .photo-item-card.marked-delete {
          border: 2px solid var(--coral);
          background: #fff1f2;
        }
    
        .photo-item-card.marked-delete .photo-thumb-wrap {
          opacity: 0.55;
          filter: grayscale(40%);
        }
    
        .delete-strike-overlay {
          display: none;
          position: absolute;
          top: 10px;
          left: 10px;
          background: var(--coral);
          color: white;
          font-size: 0.75rem;
          font-weight: 700;
          padding: 4px 8px;
          border-radius: 6px;
          z-index: 10;
          box-shadow: 0 2px 6px rgba(244,63,94,0.4);
        }
    
        .photo-item-card.marked-delete .delete-strike-overlay {
          display: inline-block;
        }
    
        .burst-badge {
          position: absolute;
          top: 10px;
          right: 10px;
          background: rgba(15, 23, 42, 0.75);
          backdrop-filter: blur(4px);
          color: #38bdf8;
          font-size: 0.72rem;
          font-weight: 700;
          padding: 3px 8px;
          border-radius: 6px;
          z-index: 9;
          display: inline-flex;
          align-items: center;
          gap: 4px;
        }
    
        .photo-thumb-wrap {
          position: relative;
          aspect-ratio: 4 / 3;
          background: #f1f5f9;
          cursor: pointer;
          overflow: hidden;
        }
    
        .photo-thumb-wrap img {
          width: 100%;
          height: 100%;
          object-fit: cover;
          display: block;
          transition: transform 0.3s ease;
        }
    
        .photo-thumb-wrap:hover img {
          transform: scale(1.04);
        }
    
        .photo-thumb-wrap.video-wrap {
          aspect-ratio: 16 / 9;
          background: #0f172a;
        }
    
        .video-play-btn {
          position: absolute;
          inset: 0;
          display: flex;
          align-items: center;
          justify-content: center;
          background: rgba(0,0,0,0.35);
          color: white;
          transition: background 0.2s;
        }
    
        .photo-thumb-wrap:hover .video-play-btn {
          background: rgba(0,0,0,0.15);
        }
    
        .play-circle {
          width: 48px;
          height: 48px;
          border-radius: 50%;
          background: white;
          color: #0f172a;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 1.3rem;
          box-shadow: 0 4px 10px rgba(0,0,0,0.3);
          transition: transform 0.2s;
        }
    
        .photo-thumb-wrap:hover .play-circle {
          transform: scale(1.1);
        }
    
        /* Card Footer Info */
        .card-footer-info {
          padding: 10px 14px;
          background: #ffffff;
          border-top: 1px solid var(--border);
          display: flex;
          flex-direction: column;
          gap: 8px;
        }
    
        .card-id-row {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 8px;
        }
    
        .photo-id-tag {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          background: #0284c7;
          color: white;
          font-weight: 800;
          font-size: 0.92rem;
          padding: 3px 10px;
          border-radius: 6px;
          letter-spacing: 0.03em;
          font-family: 'Plus Jakarta Sans', sans-serif;
        }
    
        .photo-time-label {
          font-size: 0.75rem;
          color: var(--text-muted);
          font-family: 'Plus Jakarta Sans', sans-serif;
        }
    
        .photo-filename-label {
          font-size: 0.72rem;
          color: #64748b;
          font-family: monospace;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
          background: #f8fafc;
          padding: 3px 6px;
          border-radius: 4px;
          border: 1px solid #f1f5f9;
        }
    
        .delete-action-row {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding-top: 4px;
          border-top: 1px dashed var(--border);
        }
    
        .delete-check-label {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          font-size: 0.8rem;
          font-weight: 600;
          color: #64748b;
          cursor: pointer;
          user-select: none;
          transition: color 0.2s;
        }
    
        .delete-check-label:hover {
          color: var(--coral);
        }
    
        .delete-checkbox {
          width: 17px;
          height: 17px;
          accent-color: var(--coral);
          cursor: pointer;
        }
    
        .marked-delete .delete-check-label {
          color: var(--coral);
          font-weight: 700;
        }
    
        .zoom-btn-small {
          background: transparent;
          border: none;
          color: var(--primary);
          font-size: 0.75rem;
          font-weight: 600;
          cursor: pointer;
          display: inline-flex;
          align-items: center;
          gap: 3px;
        }
    
        .zoom-btn-small:hover {
          text-decoration: underline;
        }
    
        /* 
          ======================================================
          削除機能の切り替え（一旦非表示・後で即時復活可能）
          ======================================================
          デフォルトでは body に delete-mode-active クラスが付かないため非表示。
          JS の ENABLE_DELETE_MODE を true にするか、
          console で toggleDeleteMode(true) を呼ぶと即座に全削除UIが復活します。
        */
        body:not(.delete-mode-active) .delete-assistant-bar,
        body:not(.delete-mode-active) .delete-action-row,
        body:not(.delete-mode-active) .delete-strike-overlay,
        body:not(.delete-mode-active) .burst-badge {
          display: none !important;
        }
    
        /* Sticky Bottom Delete Assistant Bar (Active when delete-mode is on) */
        .delete-assistant-bar {
          position: fixed;
          bottom: 0;
          left: 0;
          right: 0;
          z-index: 950;
          background: rgba(15, 23, 42, 0.96);
          backdrop-filter: blur(12px);
          border-top: 1px solid rgba(255, 255, 255, 0.15);
          color: white;
          padding: 12px 24px;
          box-shadow: 0 -8px 25px rgba(0,0,0,0.3);
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 16px;
          flex-wrap: wrap;
        }
    
        .assistant-left {
          display: flex;
          align-items: center;
          gap: 12px;
        }
    
        .assistant-badge {
          background: var(--coral);
          color: white;
          font-weight: 800;
          font-size: 0.85rem;
          padding: 4px 10px;
          border-radius: 999px;
          display: inline-flex;
          align-items: center;
          gap: 4px;
        }
    
        .assistant-desc {
          font-size: 0.85rem;
          color: #e2e8f0;
        }
    
        .assistant-actions {
          display: flex;
          align-items: center;
          gap: 8px;
          flex-wrap: wrap;
        }
    
        .asst-btn {
          padding: 6px 14px;
          border-radius: 8px;
          font-size: 0.825rem;
          font-weight: 700;
          cursor: pointer;
          border: none;
          transition: all 0.2s;
        }
    
        .asst-btn-copy {
          background: #38bdf8;
          color: #0f172a;
        }
        .asst-btn-copy:hover {
          background: #7dd3fc;
        }
    
        .asst-btn-cmd {
          background: #10b981;
          color: white;
        }
        .asst-btn-cmd:hover {
          background: #34d399;
        }
    
        .asst-btn-clear {
          background: rgba(255, 255, 255, 0.2);
          color: white;
        }
        .asst-btn-clear:hover {
          background: rgba(255, 255, 255, 0.3);
        }
    
        /* Lightbox Modal */
        .lightbox-modal {
          display: none;
          position: fixed;
          inset: 0;
          z-index: 1000;
          background: rgba(10, 15, 26, 0.96);
          backdrop-filter: blur(16px);
          flex-direction: column;
          color: white;
        }
    
        .lightbox-modal.active {
          display: flex;
        }
    
        .lb-header {
          padding: 16px 24px;
          display: flex;
          align-items: center;
          justify-content: space-between;
          border-bottom: 1px solid rgba(255, 255, 255, 0.1);
          background: rgba(0, 0, 0, 0.4);
        }
    
        .lb-title-group {
          display: flex;
          align-items: center;
          gap: 12px;
          flex-wrap: wrap;
        }
    
        .lb-id-badge {
          background: var(--primary);
          color: white;
          font-weight: 800;
          font-size: 0.95rem;
          padding: 4px 10px;
          border-radius: 6px;
          font-family: 'Plus Jakarta Sans', sans-serif;
        }
    
        .lb-title {
          font-size: 1.05rem;
          font-weight: 700;
        }
    
        .lb-counter {
          font-size: 0.85rem;
          color: #94a3b8;
          font-family: 'Plus Jakarta Sans', sans-serif;
        }
    
        .lb-close-btn {
          background: rgba(255, 255, 255, 0.15);
          border: none;
          color: white;
          width: 40px;
          height: 40px;
          border-radius: 50%;
          font-size: 1.25rem;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: background 0.2s;
        }
    
        .lb-close-btn:hover {
          background: rgba(255, 255, 255, 0.3);
        }
    
        .lb-body {
          flex: 1;
          position: relative;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 16px;
          overflow: hidden;
        }
    
        .lb-media-container {
          max-width: 100%;
          max-height: 100%;
          display: flex;
          align-items: center;
          justify-content: center;
        }
    
        .lb-media-container img {
          max-width: 90vw;
          max-height: 75vh;
          object-fit: contain;
          border-radius: 8px;
          box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        }
    
        .lb-media-container video {
          max-width: 90vw;
          max-height: 75vh;
          border-radius: 8px;
          outline: none;
          box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        }
    
        .lb-nav-btn {
          position: absolute;
          top: 50%;
          transform: translateY(-50%);
          width: 52px;
          height: 52px;
          border-radius: 50%;
          background: rgba(255, 255, 255, 0.15);
          border: none;
          color: white;
          font-size: 2.2rem;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          transition: background 0.2s, transform 0.2s;
          z-index: 10;
          user-select: none;
          line-height: 1;
        }
    
        .lb-nav-btn:hover {
          background: rgba(255, 255, 255, 0.3);
          transform: translateY(-50%) scale(1.08);
        }
    
        .lb-nav-prev { left: 24px; }
        .lb-nav-next { right: 24px; }
    
        .lb-footer {
          padding: 14px 24px;
          background: rgba(0, 0, 0, 0.5);
          border-top: 1px solid rgba(255, 255, 255, 0.1);
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 16px;
          flex-wrap: wrap;
        }
    
        .lb-meta-info {
          font-size: 0.85rem;
          color: #cbd5e1;
          display: flex;
          align-items: center;
          gap: 16px;
          flex-wrap: wrap;
        }
    
        .lb-actions {
          display: flex;
          align-items: center;
          gap: 10px;
          flex-wrap: wrap;
        }
    
        .lb-action-btn {
          padding: 6px 14px;
          border-radius: 6px;
          font-size: 0.825rem;
          font-weight: 600;
          text-decoration: none;
          color: white;
          background: rgba(255, 255, 255, 0.15);
          transition: background 0.2s;
        }
    
        .lb-action-btn:hover {
          background: rgba(255, 255, 255, 0.25);
        }
    
        .lb-delete-toggle-btn {
          display: none;
          background: rgba(244, 63, 94, 0.25);
          border: 1px solid var(--coral);
          color: #fecdd3;
          padding: 6px 14px;
          border-radius: 6px;
          font-size: 0.825rem;
          font-weight: 700;
          cursor: pointer;
          transition: all 0.2s;
        }
    
        body.delete-mode-active .lb-delete-toggle-btn {
          display: inline-flex;
        }
    
        .lb-delete-toggle-btn.active {
          background: var(--coral);
          color: white;
        }
    
        /* Footer */
        footer {
          background: #0f172a;
          color: #94a3b8;
          padding: 16px 20px;
          text-align: center;
          border-top: 1px solid var(--border);
        }
    
        .footer-inner {
          max-width: 600px;
          margin: 0 auto;
        }
    
        .footer-badge {
          display: inline-block;
          padding: 4px 12px;
          background: rgba(255, 255, 255, 0.08);
          border-radius: 999px;
          font-size: 0.75rem;
          font-weight: 700;
          letter-spacing: 0.08em;
          margin-bottom: 12px;
          color: #38bdf8;
        }
    
        /* Toast Notification */
        .toast-popup {
          position: fixed;
          top: 24px;
          left: 50%;
          transform: translateX(-50%) translateY(-100px);
          background: #0f172a;
          color: white;
          padding: 12px 24px;
          border-radius: 999px;
          font-size: 0.9rem;
          font-weight: 600;
          box-shadow: 0 10px 25px rgba(0,0,0,0.3);
          z-index: 2000;
          opacity: 0;
          pointer-events: none;
          transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
          border: 1px solid rgba(255, 255, 255, 0.2);
        }
    
        .toast-popup.show {
          transform: translateX(-50%) translateY(0);
          opacity: 1;
        }
    
        /* Responsive Breakpoints */
        @media (max-width: 1023px) {
          .sidebar {
            position: fixed;
            top: 0;
            left: 0;
            bottom: 0;
            transform: translateX(-100%);
            transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1);
            z-index: 1000;
          }
    
          .sidebar.open {
            transform: translateX(0);
          }
    
          .sidebar-close-btn {
            display: block;
          }
    
          .mobile-top-bar {
            display: flex;
          }
    
          .sidebar-backdrop.open {
            display: block;
          }
        }
    
        @media (max-width: 640px) {
          .spot-header {
            padding: 16px 20px;
          }
          .spot-note-box {
            padding: 12px 20px;
          }
          .media-grid {
            grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
            gap: 12px;
            padding: 16px 20px 20px;
          }
          .lb-nav-btn {
            width: 42px;
            height: 42px;
            font-size: 1.8rem;
          }
          .lb-nav-prev { left: 10px; }
          .lb-nav-next { right: 10px; }
        }
      </style>
    </head>
    <body>
    
      <!-- Toast Notification -->
      <div class="toast-popup" id="toastPopup">通知</div>
    
      <!-- Mobile Drawer Backdrop -->
      <div class="sidebar-backdrop" id="sidebarBackdrop" onclick="closeSidebar()"></div>
    
      <div class="app-layout">
        <!-- Left Sidebar Navigation -->
        <aside class="sidebar" id="sidebar">
          <div class="sidebar-header">
            <div class="sidebar-title-area" onclick="jumpToTop()" title="トップページへ戻る" role="button" tabindex="0">
              <div class="sidebar-brand">🌴 宮古島 2026</div>
              <div class="sidebar-sub">スポット案内 (全14箇所)</div>
            </div>
            <button class="sidebar-close-btn" id="sidebarCloseBtn" onclick="closeSidebar()" aria-label="閉じる">✕</button>
          </div>
    
          <!-- Filters in Sidebar -->
          <div class="sidebar-filters-box">
            <div class="sidebar-section-label">日程で絞り込み</div>
            <div class="filter-pills-row">
              <button class="filter-btn active" data-filter="all">全日程</button>
              <button class="filter-btn" data-filter="day-23">Day 1</button>
              <button class="filter-btn" data-filter="day-24">Day 2</button>
              <button class="filter-btn" data-filter="day-25">Day 3</button>
            </div>
          </div>
    
          <!-- Spots List in Sidebar -->
          <nav class="sidebar-nav-container" id="sidebarNavContainer">
    """ + sidebar_spots_str + """
          </nav>
        </aside>
    
        <!-- Main Content Area -->
        <div class="main-body">
          <!-- Mobile Sticky Top Bar -->
          <header class="mobile-top-bar">
            <button class="mobile-menu-btn" onclick="openSidebar()">☰ スポット一覧</button>
            <div class="mobile-brand-title" onclick="jumpToTop()" title="トップページへ戻る" role="button" tabindex="0">宮古島アルバム 2026</div>
            <button type="button" class="mobile-qr-btn" onclick="openQrModal()" title="QRコードを表示">
              <img src="qrcode.png" alt="QR" class="qr-trigger-icon">
              <span>QR表示</span>
            </button>
          </header>
    
          <!-- Hero Header -->
          <header class="hero">
            <!-- Small QR Trigger Button at Top Left -->
            <button type="button" class="hero-qr-trigger-btn" onclick="openQrModal()" title="スマホ連携 QRコードを表示">
              <img src="qrcode.png" alt="QR" class="qr-trigger-icon">
              <span>QR表示</span>
            </button>

            <div class="hero-inner">
              <h1>宮古島 トリップアルバム</h1>
              <p class="lead">平良の夜会食、宮古ブルーの海岸線、東平安名埼灯台、地下ダムなど。<br>3日間旅程のフォトギャラリー。</p>
    
              <div class="stats-bar">
                <div class="stat-box">
                  <div class="stat-num">""" + str(len(data['spots'])) + """</div>
                  <div class="stat-lbl">訪問スポット</div>
                </div>
                <div class="stat-box">
                  <div class="stat-num">""" + str(data['total_images']) + """</div>
                  <div class="stat-lbl">写真（Web最適化）</div>
                </div>
                <div class="stat-box">
                  <div class="stat-num">""" + str(data['total_videos']) + """</div>
                  <div class="stat-lbl">動画（高画質HD）</div>
                </div>
                <div class="stat-box">
                  <div class="stat-num">3 Days</div>
                  <div class="stat-lbl">Day 1 〜 Day 3</div>
                </div>
              </div>
            </div>
          </header>
    
          <!-- Spot Sections -->
          <main class="main-content" id="mainContent">
    """ + route_map_html + all_sections_str + """
          </main>
    
          <!-- Footer -->
          <footer>
            <div class="footer-inner">
              <p style="font-size: 0.75rem; opacity: 0.7; margin: 0;">© 2026 Miyakojima Trip Album</p>
            </div>
          </footer>
        </div>
      </div>
    
      <!-- Sticky Bottom Delete Assistant Bar (Hidden by default, can be toggled anytime) -->
      <aside class="delete-assistant-bar" id="deleteAssistantBar">
        <div class="assistant-left">
          <div class="assistant-badge">🗑️ 削除候補: <span id="deleteCount">0</span>件</div>
          <div class="assistant-desc">重複・不要写真にチェックを入れてコピーすると、一括削除コマンドを取得できます。</div>
        </div>
        <div class="assistant-actions">
          <button class="asst-btn asst-btn-copy" onclick="copyDeleteList()">📋 ファイル名一覧コピー</button>
          <button class="asst-btn asst-btn-cmd" onclick="copyPowerShellCommand()">⚡ PowerShell削除コマンド</button>
          <button class="asst-btn asst-btn-clear" onclick="clearAllDeletes()">全解除</button>
        </div>
      </aside>
    
      <!-- QR Code Zoom Modal -->
      <div class="qr-modal-overlay" id="qrModal" onclick="closeQrModal(event)">
        <div class="qr-modal-dialog" onclick="event.stopPropagation()">
          <button type="button" class="qr-modal-close-btn" onclick="closeQrModal(event)" title="閉じる (ESC)">✕</button>
          <span class="qr-modal-pill">📱 SMARTPHONE ACCESS</span>
          <h3 class="qr-modal-heading">宮古島 トリップアルバム 2026</h3>
          <p class="qr-modal-subtitle">スマホのカメラをかざすと、このアルバムが開きます</p>
          <div class="qr-modal-frame">
            <img src="qrcode.png" alt="宮古島アルバム Web URL QRコード" class="qr-modal-large-img" width="210" height="210">
          </div>
          <div>
            <button type="button" class="qr-modal-action-close" onclick="closeQrModal(event)">
              閉じる
            </button>
          </div>
        </div>
      </div>
    
      <!-- Floating Back to Map Button -->
      <button type="button" class="floating-map-btn" id="floatingMapBtn" onclick="jumpToSpot('routeMapSection')" title="宮古島ルートマップへ移動">
        <span class="floating-map-icon">🗺️</span>
        <span>マップへ戻る</span>
      </button>
    
      <!-- Lightbox Modal -->
      <div class="lightbox-modal" id="lightboxModal">
        <div class="lb-header">
          <div class="lb-title-group">
            <span class="lb-id-badge" id="lbIdBadge">A-01</span>
            <span class="lb-title" id="lbTitle">Spot Name</span>
            <span class="lb-counter" id="lbCounter">1 / """ + str(data['total_files']) + """</span>
          </div>
          <button class="lb-close-btn" onclick="closeLightbox()" title="閉じる (ESC)">✕</button>
        </div>
    
        <div class="lb-body">
          <button class="lb-nav-btn lb-nav-prev" onclick="navLightbox(-1)" title="前へ (←)">‹</button>
          <div class="lb-media-container" id="lbMediaContainer">
            <!-- Image or Video injected by JS -->
          </div>
          <button class="lb-nav-btn lb-nav-next" onclick="navLightbox(1)" title="次へ (→)">›</button>
        </div>
    
        <div class="lb-footer">
          <div class="lb-meta-info" id="lbMetaInfo">
            <!-- Date, filename -->
          </div>
          <div class="lb-actions">
            <button class="lb-delete-toggle-btn" id="lbDeleteToggleBtn" onclick="toggleCurrentItemDelete()">🗑️ この写真を削除候補にする</button>
            <a href="#" target="_blank" rel="noopener" id="lbMapBtn" class="lb-action-btn">📍 撮影地点の地図</a>
            <a href="#" target="_blank" download id="lbDownloadBtn" class="lb-action-btn">⬇ 高画質を開く</a>
          </div>
        </div>
      </div>
    
      <script>
        /* 
          =======================================================
          設定スイッチ: 削除機能の表示/非表示
          =======================================================
          false: 削除チェックボックス・アシスタントバーを非表示（現在）
          true: 削除機能を表示（後ですぐ復活可能）
        */
        const ENABLE_DELETE_MODE = false;
    
        if (ENABLE_DELETE_MODE) {
          document.body.classList.add('delete-mode-active');
        }
    
        // コンソールやデバッグで即座に切り替えられる関数
        window.toggleDeleteMode = function(enable) {
          if (enable === undefined) {
            document.body.classList.toggle('delete-mode-active');
          } else if (enable) {
            document.body.classList.add('delete-mode-active');
          } else {
            document.body.classList.remove('delete-mode-active');
          }
          const isActive = document.body.classList.contains('delete-mode-active');
          showToast(isActive ? '削除整理モードを有効にしました' : '削除整理モードを非表示にしました');
          return isActive;
        };
    
        const ALL_ITEMS = """ + json_items_str + """;
        const ALL_SPOTS = """ + json_spots_str + """;
        const itemMap = {};
        ALL_ITEMS.forEach(it => itemMap[it.id] = it);
        const spotMap = {};
        ALL_SPOTS.forEach(sp => spotMap[sp.id] = sp);
    
        let currentItemIndex = 0;
        let visibleItemIds = ALL_ITEMS.map(it => it.id);
        const markedDeleteIds = new Set();
    
        // Mobile Sidebar Drawer
        const sidebarEl = document.getElementById('sidebar');
        const backdropEl = document.getElementById('sidebarBackdrop');
    
        function openSidebar() {
          sidebarEl.classList.add('open');
          backdropEl.classList.add('open');
          document.body.style.overflow = 'hidden';
        }
    
        function closeSidebar() {
          sidebarEl.classList.remove('open');
          backdropEl.classList.remove('open');
          document.body.style.overflow = '';
        }
    
        function onSidebarNavClick(e, spotId) {
          if (window.innerWidth < 1024) {
            closeSidebar();
          }
          jumpToSpot(spotId);
        }
    
        function jumpToTop() {
          if (window.innerWidth < 1024) {
            closeSidebar();
          }
          window.scrollTo({
            top: 0,
            behavior: 'smooth'
          });
          document.querySelectorAll('.sidebar-spot-link').forEach(link => link.classList.remove('active'));
        }
    
        function showToast(msg) {
          const t = document.getElementById('toastPopup');
          t.textContent = msg;
          t.classList.add('show');
          setTimeout(() => t.classList.remove('show'), 2500);
        }
    
        // Filter Buttons Logic
        document.querySelectorAll('.filter-btn').forEach(btn => {
          btn.addEventListener('click', () => {
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            const filter = btn.getAttribute('data-filter');
            applyFilter(filter);
          });
        });
    
        function applyFilter(filter) {
          const sections = document.querySelectorAll('.spot-section');
          visibleItemIds = [];
    
          sections.forEach(sec => {
            const category = sec.getAttribute('data-category');
            const day = sec.getAttribute('data-day');
            const secId = sec.getAttribute('id');
            const navLink = document.getElementById('nav-link-' + secId);
    
            let showSec = false;
            if (filter === 'all') showSec = true;
            else if (filter === 'day-23' && day === 'day-23') showSec = true;
            else if (filter === 'day-24' && day === 'day-24') showSec = true;
            else if (filter === 'day-25' && day === 'day-25') showSec = true;
    
            sec.style.display = showSec ? 'block' : 'none';
            if (navLink) {
              navLink.style.display = showSec ? 'flex' : 'none';
            }
    
            if (showSec) {
              const cards = sec.querySelectorAll('.photo-item-card');
              cards.forEach(card => {
                card.style.display = 'flex';
                visibleItemIds.push(card.getAttribute('data-item-id'));
              });
            }
          });
        }
    
        function jumpToSpot(spotId) {
          if (!spotId) return;
          const target = document.getElementById(spotId);
          if (target) {
            target.style.display = 'block';
            target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            highlightNav(spotId);
          }
        }
    
        function highlightNav(spotId) {
          document.querySelectorAll('.sidebar-spot-link').forEach(link => {
            if (link.getAttribute('data-spot-id') === spotId) {
              link.classList.add('active');
            } else {
              link.classList.remove('active');
            }
          });
        }
    
        // IntersectionObserver for active spot highlight on scroll
        const observer = new IntersectionObserver((entries) => {
          entries.forEach(entry => {
            if (entry.isIntersecting) {
              const id = entry.target.getAttribute('id');
              highlightNav(id);
            }
          });
        }, {
          root: null,
          rootMargin: '-20% 0px -60% 0px',
          threshold: 0
        });
    
        document.querySelectorAll('.spot-section').forEach(sec => {
          observer.observe(sec);
        });
    
        // Delete Management
        function toggleItemDelete(itemId, isChecked) {
          const card = document.getElementById('card-' + itemId);
          const chk = card ? card.querySelector('.delete-checkbox') : null;
          if (isChecked) {
            markedDeleteIds.add(itemId);
            if (card) card.classList.add('marked-delete');
            if (chk) chk.checked = true;
          } else {
            markedDeleteIds.delete(itemId);
            if (card) card.classList.remove('marked-delete');
            if (chk) chk.checked = false;
          }
          updateDeleteAssistant();
          updateLightboxDeleteBtn();
        }
    
        function updateDeleteAssistant() {
          const countEl = document.getElementById('deleteCount');
          if (countEl) countEl.textContent = markedDeleteIds.size;
        }
    
        function clearAllDeletes() {
          markedDeleteIds.clear();
          document.querySelectorAll('.photo-item-card').forEach(c => c.classList.remove('marked-delete'));
          document.querySelectorAll('.delete-checkbox').forEach(chk => chk.checked = false);
          updateDeleteAssistant();
          updateLightboxDeleteBtn();
          showToast('削除候補の選択をすべて解除しました');
        }
    
        function copyDeleteList() {
          if (markedDeleteIds.size === 0) {
            alert('削除候補の写真が選択されていません。');
            return;
          }
          const list = Array.from(markedDeleteIds).map(id => {
            const it = itemMap[id];
            return it.custom_id + ' : ' + it.filename;
          });
          navigator.clipboard.writeText(list.join('\\n')).then(() => {
            showToast('選択した ' + markedDeleteIds.size + ' 件のファイル名一覧をコピーしました！');
          });
        }
    
        function copyPowerShellCommand() {
          if (markedDeleteIds.size === 0) {
            alert('削除候補の写真が選択されていません。');
            return;
          }
          const files = Array.from(markedDeleteIds).map(id => itemMap[id].filename);
          const quotedFiles = files.map(f => '"' + f + '"').join(', ');
          const cmd = '$files = @(' + quotedFiles + '); foreach($f in $files) { $base = [System.IO.Path]::GetFileNameWithoutExtension($f); Remove-Item "images\\\\web\\\\$base.jpg", "images\\\\thumb\\\\$base.jpg", "videos\\\\$f" -ErrorAction SilentlyContinue; Write-Host "Deleted: $f" }';
          navigator.clipboard.writeText(cmd).then(() => {
            showToast('PowerShell削除コマンド（' + files.length + '件）をコピーしました！');
          });
        }
    
        // Lightbox Logic
        const modal = document.getElementById('lightboxModal');
        const container = document.getElementById('lbMediaContainer');
        const idBadge = document.getElementById('lbIdBadge');
        const titleEl = document.getElementById('lbTitle');
        const counterEl = document.getElementById('lbCounter');
        const metaEl = document.getElementById('lbMetaInfo');
        const mapBtn = document.getElementById('lbMapBtn');
        const dlBtn = document.getElementById('lbDownloadBtn');
        const lbDelBtn = document.getElementById('lbDeleteToggleBtn');
    
        function openLightbox(itemId) {
          const idx = visibleItemIds.indexOf(itemId);
          currentItemIndex = idx >= 0 ? idx : 0;
          renderLightbox();
          modal.classList.add('active');
          document.body.style.overflow = 'hidden';
        }
    
        function closeLightbox() {
          modal.classList.remove('active');
          container.innerHTML = '';
          document.body.style.overflow = '';
        }
    
        function navLightbox(delta) {
          if (visibleItemIds.length === 0) return;
          currentItemIndex = (currentItemIndex + delta + visibleItemIds.length) % visibleItemIds.length;
          renderLightbox();
        }
    
        function toggleCurrentItemDelete() {
          const itemId = visibleItemIds[currentItemIndex];
          const isMarked = markedDeleteIds.has(itemId);
          toggleItemDelete(itemId, !isMarked);
        }
    
        function updateLightboxDeleteBtn() {
          const itemId = visibleItemIds[currentItemIndex];
          if (!itemId || !lbDelBtn) return;
          const isMarked = markedDeleteIds.has(itemId);
          if (isMarked) {
            lbDelBtn.classList.add('active');
            lbDelBtn.innerHTML = '🗑️ 削除候補から解除';
          } else {
            lbDelBtn.classList.remove('active');
            lbDelBtn.innerHTML = '🗑️ この写真を削除候補にする';
          }
        }
    
        function renderLightbox() {
          const itemId = visibleItemIds[currentItemIndex];
          const item = itemMap[itemId];
          if (!item) return;
    
          const spot = spotMap[item.spot_id] || { title: '' };
          idBadge.textContent = item.custom_id;
          titleEl.textContent = spot.title;
          counterEl.textContent = (currentItemIndex + 1) + ' / ' + visibleItemIds.length;
    
          container.innerHTML = '';
          if (item.type === 'image') {
            const img = document.createElement('img');
            img.src = item.web_file;
            img.alt = item.filename;
            container.appendChild(img);
            dlBtn.href = item.web_file;
            dlBtn.textContent = '🔍 Web版を開く';
          } else {
            const video = document.createElement('video');
            video.src = item.video_file;
            video.controls = true;
            video.autoplay = true;
            video.playsInline = true;
            container.appendChild(video);
            dlBtn.href = item.video_file;
            dlBtn.textContent = '🎬 動画を別窓で開く';
          }
    
          metaEl.innerHTML = `
            <span>📅 ${item.datetime || ''}</span>
            ${item.size_web ? '<span>💾 ' + (item.size_web / 1024).toFixed(0) + ' KB</span>' : ''}
          `;
    
          if (item.lat && item.lon) {
            mapBtn.style.display = 'inline-flex';
            mapBtn.href = 'https://www.google.com/maps/search/?api=1&query=' + item.lat + ',' + item.lon;
          } else {
            mapBtn.style.display = 'none';
          }
    
          updateLightboxDeleteBtn();
        }
    
        // QR Code Modal & URL Copy Helpers
        function copyAlbumUrl(btn) {
          const url = 'https://dzr01145.github.io/miyakojima-album-2026/';
          if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(url).then(() => {
              const orig = btn.innerHTML;
              btn.innerHTML = '✅ コピー完了！';
              btn.style.background = '#10b981';
              btn.style.color = '#ffffff';
              setTimeout(() => {
                btn.innerHTML = orig;
                btn.style.background = '';
                btn.style.color = '';
              }, 2000);
            }).catch(() => {
              fallbackCopy(url, btn);
            });
          } else {
            fallbackCopy(url, btn);
          }
        }
    
        function fallbackCopy(url, btn) {
          const ta = document.createElement('textarea');
          ta.value = url;
          ta.style.position = 'fixed';
          ta.style.opacity = '0';
          document.body.appendChild(ta);
          ta.select();
          try {
            document.execCommand('copy');
            const orig = btn.innerHTML;
            btn.innerHTML = '✅ コピー完了！';
            btn.style.background = '#10b981';
            btn.style.color = '#ffffff';
            setTimeout(() => {
              btn.innerHTML = orig;
              btn.style.background = '';
              btn.style.color = '';
            }, 2000);
          } catch (e) {
            prompt('以下のURLをコピーしてください:', url);
          }
          document.body.removeChild(ta);
        }
    
        function openQrModal() {
          const modal = document.getElementById('qrModal');
          if (modal) modal.classList.add('active');
        }
    
        function closeQrModal(e) {
          if (e) e.stopPropagation();
          const modal = document.getElementById('qrModal');
          if (modal) modal.classList.remove('active');
        }
    
        // Floating Map Button Scroll Listener
        window.addEventListener('scroll', () => {
          const mapEl = document.getElementById('routeMapSection');
          const fab = document.getElementById('floatingMapBtn');
          if (mapEl && fab) {
            const mapRect = mapEl.getBoundingClientRect();
            // Show floating button when map is scrolled past (bottom of map is above upper viewport)
            if (mapRect.bottom < 100) {
              fab.classList.add('visible');
            } else {
              fab.classList.remove('visible');
            }
          }
        });
    
        // Pop Route Map Interactivity
        function jumpToSpot(spotId) {
          const el = document.getElementById(spotId);
          if (el) {
            const offset = 70;
            const bodyRect = document.body.getBoundingClientRect().top;
            const elementRect = el.getBoundingClientRect().top;
            const elementPosition = elementRect - bodyRect;
            const offsetPosition = elementPosition - offset;
            window.scrollTo({
              top: offsetPosition,
              behavior: 'smooth'
            });
            el.style.transition = 'box-shadow 0.3s ease';
            el.style.boxShadow = '0 0 0 4px #38bdf8, 0 10px 25px rgba(2, 132, 199, 0.25)';
            setTimeout(() => {
              el.style.boxShadow = '';
            }, 1600);
          }
        }
    
        function setMapRouteFilter(dayFilter, btn) {
          document.querySelectorAll('.map-route-btn').forEach(b => b.classList.remove('active'));
          if (btn) btn.classList.add('active');
    
          const d2Lines = document.querySelectorAll('.day2-route, #day2RouteLayer');
          const d3Lines = document.querySelectorAll('.day3-route, #day3RouteLayer');
          const allPins = document.querySelectorAll('.map-pin-group');
    
          if (dayFilter === 'all') {
            d2Lines.forEach(el => el.classList.remove('dimmed'));
            d3Lines.forEach(el => el.classList.remove('dimmed'));
            allPins.forEach(p => p.classList.remove('dimmed'));
          } else if (dayFilter === 'day-23') {
            d2Lines.forEach(el => el.classList.add('dimmed'));
            d3Lines.forEach(el => el.classList.add('dimmed'));
            allPins.forEach(p => {
              if (p.getAttribute('data-day') === 'day-23') p.classList.remove('dimmed');
              else p.classList.add('dimmed');
            });
          } else if (dayFilter === 'day-24') {
            d2Lines.forEach(el => el.classList.remove('dimmed'));
            d3Lines.forEach(el => el.classList.add('dimmed'));
            allPins.forEach(p => {
              if (p.getAttribute('data-day') === 'day-24' || p.getAttribute('data-spot-id') === 'spot-01') p.classList.remove('dimmed');
              else p.classList.add('dimmed');
            });
          } else if (dayFilter === 'day-25') {
            d2Lines.forEach(el => el.classList.add('dimmed'));
            d3Lines.forEach(el => el.classList.remove('dimmed'));
            allPins.forEach(p => {
              if (p.getAttribute('data-day') === 'day-25' || p.getAttribute('data-spot-id') === 'spot-09') p.classList.remove('dimmed');
              else p.classList.add('dimmed');
            });
          }
        }
    
        // Keyboard controls
        document.addEventListener('keydown', (e) => {
          if (!modal.classList.contains('active')) return;
          if (e.key === 'Escape') { closeLightbox(); closeQrModal(); }
          else if (e.key === 'ArrowLeft') navLightbox(-1);
          else if (e.key === 'ArrowRight') navLightbox(1);
        });
    
        document.querySelector('.sidebar-title-area')?.addEventListener('keydown', (e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            jumpToTop();
          }
        });
      </script>
    </body>
    </html>
    """
    
    # Write index.html (UTF-8 without BOM)
    with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
        f.write(html_template)
    print(f"Generated {OUTPUT_HTML} successfully (Size: {os.path.getsize(OUTPUT_HTML):,} bytes).")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Build Travel Web Album with Sidebar & Route Map")
    parser.add_argument("--data", default="album_data.json", help="Path to album_data.json")
    parser.add_argument("--output", default="index.html", help="Output HTML path")
    parser.add_argument("--base-dir", default=".", help="Base directory of album")
    args = parser.parse_args()
    build_album(args.data, args.output, args.base_dir)
