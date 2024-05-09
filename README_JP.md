# godfield-flash

このリポジトリには、フラッシュ版ゲーム「ゴッドフィールド」の歴史的なバックアップと、そのために書いたサーバーエミュレータが含まれています。

私は2016年にこのサーバーエミュレータをやったが、それは私のハードドライブで埃を集めていたので、私は今それをオープンソースにすることを決めた、私は本当にこれが消えることを望んでいない。エミュレータはかなり動作していますが、まだいくつかのマイナーなバグといくつかの不足しているものを持っています。
これはこのプロジェクトが放棄されたことを意味しません、私はまだこのサーバーエミュレータを更新し、それがより信頼性の高い、元のゲームに正確にしたい、あなたが私を助けたい場合は、問題を開くか、プルリクエストを行うこと自由に落ちた！私は、このプロジェクトに参加することをお勧めします。

## 既知の問題点

このサーバーエミュレーターは、ほぼ完璧とは言えませんが、動作します (下のMP4にあるように)ですが、現時点で覚えている問題点をいくつか挙げてみます。

- アーティファクトの分布があるべき姿ではない（要調査）。
- ボットはあまり賢くないので、彼が今使えるアーティファクトを投げるだけです。(そして、そうプログラムされている)
- "霧"の呪いは、まだ正しく実装されていません。
- クライアントのバックアップが完了していない可能性があります。
  - バックアップは、ゲームをプレイして、ゲームから要求されたものをダウンロードしたものなので、もしかしたら全部は取得していないかもしれませんし、確かに無効化されたゲームモードのファイルは取得していないかもしれません。

https://user-images.githubusercontent.com/14041768/159081100-ff837b56-2b9d-4c80-a722-9e6e32924994.mp4

## フラッシュは死んだ! どうする？

このリポジトリには、Flashで書かれた旧バージョンの「ゴッドフィールド」が含まれています。残念ながら、Flashはもうほとんどのブラウザでサポートされていません。しかし、以下の方法を使えば、まだゴッドフィールドを動かすことは可能です：

1. 最近ゴッドフィールドにかなりのサポートを得た、Flashエミュレータの[Ruffle](https://github.com/ruffle-rs/ruffle)を使用する。
2. Flashをサポートしているブラウザを使用する。
3. Flash Projector経由でゲームのSWFファイルを直接実行する。[Flash Projectorはこちらからダウンロードできます。](https://fpdownload.macromedia.com/pub/flashplayer/updaters/32/flashplayer_32_sa.exe)

## 必要条件

サーバーエミュレータを動作させるには、**Python 3.9+**が必要です。`requirements.txt`を使ってすべての依存関係をインストールしてください。方法がわかりませんか？ [要求ファイルについてはこちらをご覧ください。](https://pip.pypa.io/en/stable/user_guide/#requirements-files)

## 迅速なセットアップ

まず、以下の行を`hosts`ファイルに追加します：

```
127.0.0.1 www.godfield.net
127.0.0.1 static.godfield.net 
127.0.0.1 training.godfield.net
127.0.0.1 enfreefight.godfield.net
127.0.0.1 freefight.godfield.net
127.0.0.1 enfreefightprivate.godfield.net 
127.0.0.1 freefightprivate.godfield.net
```

*注意：後でこれらのエントリを削除してください。そうしないと、公式の「ゴッドフィールド」サイトに到達できなくなります。*

次に、`client-files`フォルダ内のスクリプト`webserver.py`を実行し、Ruffleエミュレータを使用しても問題ない場合は、`server-src`フォルダ内のスクリプト`server.py`をコマンドライン`server.py --language JP --ws`で実行します。それ以外の場合は、`server.py --language JP`だけで実行してください。

これでゲームを開く準備ができました！ウェブブラウザで`http://www.godfield.net/index.html`に移動するだけで、Ruffleを使ってゲームが実行されるはずです。Adobe Flash Playerを使用したい場合は、まだFlashをサポートしているブラウザで`http://www.godfield.net/og_index.html`に移動できます。あるいは、[Flash Projector](https://fpdownload.macromedia.com/pub/flashplayer/updaters/32/flashplayer_32_sa.exe)を使うこともできます。実行ファイルを実行してCTRL+Oを押すと、ウィンドウが表示されるはずです。このウィンドウで、`Location`テキストフィールドに`http://www.godfield.net/game/godfield.swf?language=ja&valid=1`と入力して、`OK`をクリックするだけです。

## 備考

- 私はサーバーエミュレータ（とゲームのPT-BR翻訳）を書いただけです。クライアントファイルに関するすべての権利は[@guuji](https://twitter.com/guuji)にあります。
- 私は `helpers` フォルダ内のどのファイルも作成者ではありませんが、そのうちのいくつかを少し修正しました。
