# godfield-flash

このリポジトリには、フラッシュ版ゲーム「ゴッドフィールド」と、そのために書いたサーバーエミュレータの歴史的バックアップが含まれています。

私は2016年にこのサーバーエミュレータをやったが、それは私のハードドライブで埃を集めていたので、私は今それをオープンソースにすることを決めた、私は本当にこれが消えることを望んでいない。エミュレータはかなり動作していますが、まだいくつかのマイナーなバグといくつかの不足しているものを持っています。
これはこのプロジェクトが放棄されたことを意味しません、私はまだこのサーバーエミュレータを更新し、それがより信頼性の高い、元のゲームに正確にしたい、あなたが私を助けたい場合は、問題を開くか、プルリクエストを行うこと自由に落ちた！私は、このプロジェクトに参加することをお勧めします。

## 既知の問題点

このサーバーエミュレーターは、ほぼ完璧とは言えませんが、動作します (下のMP4にあるように)ですが、現時点で覚えている問題点をいくつか挙げてみます。

- アーティファクトの分布があるべき姿ではない（要調査）。
- ボットはあまり賢くないので、彼が今使えるアーティファクトを投げるだけです。(そして、そうプログラムされている)
- 霧の効果は、呪いを取り除いても解除されません。
- クライアントのバックアップが完了していない可能性があります。
  - バックアップは、ゲームをプレイして、ゲームから要求されたものをダウンロードしたものなので、もしかしたら全部は取得していないかもしれませんし、確かに無効化されたゲームモードのファイルは取得していないかもしれません。

![Demo](https://raw.githubusercontent.com/Igoorx/godfield-flash/master/demo.mp4)

## 必要条件

サーバーエミュレータを動作させるには、「Python 3.9+」が必要です。すべての依存関係は "requirements.txt" を使ってインストールできますが、方法がわかりません？ [要求ファイルについてはこちらをご覧ください。](https://pip.pypa.io/en/stable/user_guide/#requirements-files)

## フラッシュは死んだ! どうする？

このリポジトリには、Flashで書かれた旧バージョンの「ゴッドフィールド」が含まれています。しかし、Flashはもうほとんどのブラウザでサポートされていませんが、まだサポートしているブラウザを使用するか、Flash Projector経由でゲームのswfを直接実行すれば、ゴッドフィールドを動かすことは可能ですので、ご安心ください。
[Flash Projectorはこちらからダウンロードできます。](https://fpdownload.macromedia.com/pub/flashplayer/updaters/32/flashplayer_32_sa.exe)

## 迅速なセットアップ

ゲームに参加するには、`static.godfield.net`と`www.godfield.net`フォルダの両方の内容を持つポート80で動作するWebサーバーが必要です。Webサーバーのセットアップに助けが必要な場合やそれが何かさえ分からない場合、[ここをクリックして、これはきっとあなたの助けになるでしょう。](https://stackoverflow.com/questions/45584453/how-to-create-a-simple-http-webserver-in-python). (PORTは必ず80に変更してください)
その後、hostsファイルに以下の行を追加する必要があります:

```
127.0.0.1 www.godfield.net
127.0.0.1 static.godfield.net
127.0.0.1 training.godfield.net
127.0.0.1 enfreefight.godfield.net
127.0.0.1 freefight.godfield.net
127.0.0.1 enfreefightprivate.godfield.net
127.0.0.1 freefightprivate.godfield.net
```

それを使って、pythonでサーバーエミュレータを実行し、まだFlashをサポートしているブラウザでリンク `http://www.godfield.net/en.html` を開くだけです。あるいは、["Flash Projector"](https://fpdownload.macromedia.com/pub/flashplayer/updaters/32/flashplayer_32_sa.exe)を使って、CTRL+Oを押すと、ウィンドウが表示されます。このウィンドウで、`Location`テキストフィールドに `http://www.godfield.net/game/godfield.swf` を入力して、`OK`ボタンを押すだけでよいのです。

## 備考

- 私はサーバーエミュレータ（とゲームのPT-BR翻訳）を書いただけです。クライアントファイルに関するすべての権利は[@guuji](https://twitter.com/guuji)にあります。
- 私は `helpers` フォルダ内のどのファイルも作成者ではありませんが、そのうちのいくつかを少し修正しました。
