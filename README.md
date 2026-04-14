# render_pymol_overlay.py の使い方

このスクリプトは、PyMOL を使用して構造データの重ね合わせプレビュー画像を生成するためのものです。

## 必要条件
- Python 3.x
- PyMOL 2.x
- 必要なライブラリがインストールされていること

## 実行方法

以下のコマンドを使用してスクリプトを実行します。

```bash
python render_pymol_overlay.py --known <known_structure> --set1 <set1_pattern> --set2 <set2_pattern> --out_dir <output_directory> [--method <method>] [--width <width>] [--height <height>]
```

### 引数の説明

| 引数名          | 必須 | 説明                                                                                     |
|-----------------|------|------------------------------------------------------------------------------------------|
| `--known`       | 必須 | 既知の構造ファイル (PDB または CIF ファイル) のパス                                     |
| `--set1`        | 必須 | セット1の構造ファイルの glob パターン (例: `set1/*.pdb`)                                  |
| `--set2`        | 必須 | セット2の構造ファイルの glob パターン (例: `set2/*.pdb`)                                  |
| `--out_dir`     | 必須 | 出力ディレクトリのパス                                                                   |
| `--method`      | 任意 | アライメント方法 (`align` または `super`)。デフォルトは `super`                          |
| `--width`       | 任意 | 出力画像の幅 (ピクセル単位)。デフォルトは 1600                                          |
| `--height`      | 任意 | 出力画像の高さ (ピクセル単位)。デフォルトは 900                                         |

## 出力

指定した出力ディレクトリに以下のファイルが生成されます:

- `overlay_all.png`: 全ての構造を含む重ね合わせ画像
- `overlay_set1.png`: セット1の構造を含む重ね合わせ画像
- `overlay_set2.png`: セット2の構造を含む重ね合わせ画像
- `overlay_preview_session.pse`: PyMOL セッションファイル

## 使用例

以下は、既知の構造 `known.pdb` とセット1およびセット2の構造ファイルを使用して画像を生成する例です。

```bash
python render_pymol_overlay.py \
  --known known.pdb \
  --set1 "set1/*.pdb" \
  --set2 "set2/*.pdb" \
  --out_dir output \
  --method align \
  --width 1920 \
  --height 1080
```

このコマンドを実行すると、`output` ディレクトリに画像とセッションファイルが生成されます。

## 注意事項
- PyMOL の DLL パスが正しく設定されている必要があります。Windows 環境では、`PYMOL_DLL_DIR` 環境変数を設定してください。
- 入力ファイルの形式は PDB または CIF に対応しています。
