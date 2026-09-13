# 宮古島 トリップアルバム 2026 (Miyakojima Trip Album)

宮古島・伊良部島・下地島の旅程記録フォトアルバム。
時系列のスポット情報、Web最適化された高画質写真・HD動画、インタラクティブな左側ナビゲーションを備えた静的Webサイトです。

## 構成
- `index.html`: メインアルバム（レスポンシブ・サイドバーナビゲーション・ライトボックス搭載）
- `album_data.json`: 旅程および写真・動画メタデータ
- `images/web/`: Web表示用に圧縮・最適化された画像
- `images/thumb/`: 高速表示サムネイル画像
- `videos/`: 高画質・低容量（H.264+AAC）の動画
- `.gitignore`: 大容量原本（`VOID/`）および作業一時ファイルを除外

## Render へのデプロイ手順 (Static Site)
1. GitHub にリポジトリを作成し、本プロジェクトを push します。
   ```bash
   git init
   git add .
   git commit -m "Initial commit: Miyakojima Trip Album 2026"
   git branch -M main
   git remote add origin <your-github-repo-url>
   git push -u origin main
   ```
2. Render (https://render.com) にログインし、**New +** -> **Static Site** を選択。
3. GitHub リポジトリを連携。
4. 設定項目：
   - **Name**: 任意（例: `miyakojima-album-2026`）
   - **Branch**: `main`
   - **Build Command**: *(空欄のまま)*
   - **Publish Directory**: `.` *(ルートディレクトリ)*
5. **Create Static Site** をクリックすると、数十秒で公開URLが発行されます。

## 特徴
- 📍 **左側サイドバーナビゲーション**: 全14スポットへのワンクリックジャンプ、日程フィルター、スクロール連動ハイライト。
- 🔍 **ライトボックス**: 拡大表示、前後送り、キーボード操作（←/→/ESC）対応。
- 🗺️ **Google Maps 連携**: 各スポットの公式地図またはピンポイント撮影座標へ直接リンク。
- 🚀 **超軽量設計**: 全体で約48MBに最適化。モバイルでも瞬時に読み込まれます。
