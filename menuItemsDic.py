
import re


def getValueString(ref_id):
	""" ナビキーとダイアログ文字列を消去した文字列を取り出し """
	dicVal = dic[ref_id]
	s = re.sub("\.\.\.$", "", dicVal)
	s = re.sub("\(&.\)$", "", s)
	return re.sub("&", "", s)


dic = {
	"FILE_REFRESH_CHANNELS": _("チャンネル一覧を更新(&R)"),
	"FILE_EXIT": _("終了(&X)"),

	"PLAY_PLAY": _("選択中のチャンネルを再生(&P)"),
	"PLAY_STOP": _("停止(&S)"),
	"PLAY_COPY_URL": _("再生&URLのコピー"),

	"OPTION_OPTION": _("オプション(&O)") + "...",
	"OPTION_KEY_CONFIG": _("ショートカットキーの設定(&K)") + "...",

	"HELP_UPDATE": _("最新バージョンを確認(&U)") + "...",
	"HELP_VERSIONINFO": _("バージョン情報(&V)") + "...",

	"NOWPLAYING_COPY": _("選択中の内容をコピー"),
}
