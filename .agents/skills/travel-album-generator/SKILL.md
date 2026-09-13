---
name: travel-album-generator
description: >-
  写真・動画フォルダから、左側サイドバー付き高機能レスポンシブWebアルバム（EXIF自動解析・スポット自動分類・Web最適化・QRコード共有カード・ライトボックス・地図連携）を全自動で構築・公開するためのスキル。新規写真の投入時に自動実行可能。
---

# Travel Album Generator (旅行Webアルバム自動生成スキル)

## 概要
スマートフォンやデジカメ等で撮影された大量の写真・動画から、旅程やスポットごとの高品質なWebフォトアルバムを自動構築します。

### 主な特徴と自動化機能
1. **EXIF・タイムスタンプ自動解析**:
   - 撮影日時、GPS座標を自動抽出。
   - 移動時間ギャップ（20〜30分以上の間隔）や位置情報をもとにスポット（[A], [B], [C]...）へ自動クラスタリング。
2. **高速表示Web最適化**:
   - 画像: 長辺1600px（品質80）のWeb用画像と400pxサムネイルを自動生成。EXIFの向き（Orientation）を自動補正。
   - 動画: H.264/AAC（2MB未満目標）へ自動圧縮。オリジナル原本は安全に退避・保管。
3. **Glassmorphism QRコードカード & 拡大モーダル**:
   - 公開URLのQRコードをタイトルの下に配置。
   - ワンクリックURLコピー、QRコード拡大モーダル、QR画像保存機能を完備。
4. **左側サイドバー & レスポンシブUI**:
   - 日程別フィルター（Day 1, Day 2...）、スポットジャンプ、写真件数バッジ。
   - スマートフォンではハンバーガードロワーメニューとして快適に動作。
5. **フルスクリーン・ライトボックス**:
   - キーボード（← / → / ESC）やスワイプで前後の写真・動画を高画質閲覧。
   - Google Maps撮影地リンク連携。
6. **不要写真・重複整理アシスタント**:
   - 削除候補のチェックボックスから一括削除コマンドを生成可能。

---

## ワークフロー手順

### ステップ 1: 写真・動画のスキャンとスポット自動分類
撮影メディアが置かれたフォルダを指定してスキャンし、`album_data.json` を生成します。
```bash
python .agents/skills/travel-album-generator/scripts/process_album.py scan --input-dir <写真フォルダ> --output album_data.json --title "〇〇 トリップアルバム"
```

### ステップ 2: メディアのWeb最適化
Web表示用の軽量画像（`images/web/`）、サムネイル（`images/thumb/`）を自動生成します。
```bash
python .agents/skills/travel-album-generator/scripts/process_album.py optimize --data album_data.json
```

### ステップ 3: 旅程メモ・スポット情報の反映
ユーザーから提供された旅程メモ（食事場所、観光スポット名、感想など）を `album_data.json` の各スポット（`title`, `note`, `map_query`）にマッピングします。

### ステップ 4: QRコードの生成
Webアルバムの公開先URLが決まったら、QRコードを自動生成します。
```bash
python .agents/skills/travel-album-generator/scripts/process_album.py qr --url "https://<username>.github.io/<repo>/"
```

### ステップ 5: WebアルバムHTMLのビルド
HTML生成スクリプト（または既存のビルダースクリプト）を実行して `index.html` を作成します。
ファイルは必ず **UTF-8 (BOMなし)** で保存します。

### ステップ 6: GitHub / Render 公開
`git add`, `git commit`, `git push` を行い、GitHub Pages または Render で即時公開します。

---

## 遵守事項・ベストプラクティス
- **テキストエンコーディング**: すべてのテキストファイル（HTML/JSON/MD等）は必ず **UTF-8 (BOMなし)** で保存すること。
- **元ファイルの保護**: 原本写真や高画質元動画は絶対に上書きせず、`VOID/` または `originals/` フォルダへ退避保管すること。
- **プライバシー保護**: 個人情報や不要なメタデータが公開リポジトリに含まれないよう検証すること。
