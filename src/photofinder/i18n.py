"""UI language. The Traditional Chinese (Cantonese) text is the key; other languages map it to a translation.

tr("共 {n} 張", n=3) -> "共 3 張" (zh) or "3 photos" (en). A missing translation falls back to the key.
"""
LANGS = {"zh": "繁體中文", "en": "English"}
_lang = "zh"

EN = {
    # --- face picker
    "邊個係你要搵嘅人?": "Which one is the person?",
    "略過呢張": "Skip this photo",
    "揀第 {n} 個": "Pick #{n}",
    "呢張相入面有幾個人。撳相上面嘅面,或者撳下面嘅掣,揀你要搵嗰個。":
        "There are several people in this photo. Click a face, or use the buttons below, to choose who to look for.",
    # --- result grid
    "選取本頁全部": "Select page",
    "🔒 全部喺你部電腦度運算 · 原相只會讀取,唔會改動、搬走或者上載":
        "🔒 Everything runs on your computer · originals are only read, never changed, moved or uploaded",
    "上一頁": "Previous page",
    "下一頁": "Next page",
    "共 {n} 張 · 第 {p}/{t} 頁": "{n} photos · page {p}/{t}",
    "共 {n} 張": "{n} photos",
    "搵返一個人嘅所有相": "Find every photo of one person",
    "未有確認嘅相": "No confirmed photos yet",
    "俾幾張參考相,Photo Finder Pro 會喺你嘅相片資料夾入面搵晒佢出嚟,再複製一份去結果資料夾。":
        "Give it a few reference photos and Photo Finder Pro searches your photo folders for that person, "
        "then copies the matches to the results folder.",
    "試吓加多幾張唔同年份嘅參考相,或者喺「待你確認」度確認啲相。":
        "Try adding more reference photos from different years, or confirm photos in \"To review\".",
    "冇需要你確認嘅相": "Nothing to review",
    "分數喺兩個門檻之間嘅相會喺呢度出現。雙擊一張相,用 Y / N 鍵快速確認。":
        "Photos scoring between the two thresholds appear here. Double-click one and press Y / N to review quickly.",
    "未有排除嘅相": "No excluded photos",
    "標記做「唔係佢」嘅相會放喺呢度,唔會出現喺最終結果。檔案本身唔會被刪除。":
        "Photos marked \"Not them\" are kept here and left out of the final result. "
        "The files themselves are never deleted.",
    "相似度 {s}%": "Match {s}%",
    "加入相片資料夾": "Add photo folders",
    "加入參考相": "Add references",
    "撳「開始搜尋」": "Click \"Start search\"",
    # --- history
    "搜尋歷史:名、日期、資料夾…": "Filter history: name, date, folder…",
    "未有搜尋紀錄": "No searches yet",
    "完成一次搜尋之後會喺呢度出現。": "Finished searches will appear here.",
    "開啟呢個搜尋": "Open search",
    "開啟結果資料夾": "Open folder",
    "移除紀錄": "Remove",
    "只係移除紀錄,唔會刪除結果資料夾同相片": "Only removes the record; the results folder and photos are kept",
    "(未完成)": "(unfinished)",
    "{c} 確認 / {m} 待確認": "{c} confirmed / {m} to review",
    # --- top bar
    "100% 本機運算 · 私隱安全": "100% on-device · private",
    "搵邊個?例如:公公": "Who? e.g. Grandpa",
    "新搜尋": "New search",
    "開一個全新嘅搜尋(清空參考相同名)": "Start a blank search (clears references and name)",
    "切換深色 / 淺色": "Switch dark / light",
    "切換語言 / Language": "Switch language / 語言",
    "停止": "Stop",
    "停止(下次會由停低嗰度繼續)": "Stop (the next run continues from here)",
    "開始搜尋": "Start search",
    "重新開啟程式後生效": "Restart the app to apply",
    # --- sidebar
    "相片資料夾": "Photo folders",
    "可以直接拖資料夾入嚟,包括子資料夾": "Drag folders in; sub-folders are included",
    "加入資料夾": "Add folder",
    "移除": "Remove",
    "要搵嘅人": "Who to find",
    "從參考相移除": "Remove from references",
    "移除所選": "Remove",
    "全部清除": "Clear all",
    "(撳選,再按「移除所選」或者右鍵移除)": "(select it, then click \"Remove\" or right-click)",
    "{n} 張參考相,{m} 個參考臉(連鏡像)。越多張、越多年份越準。":
        "{n} reference photos, {m} reference faces (with mirrored). More photos from more years = better accuracy.",
    "未有參考相。加入幾張清楚嘅正面相。": "No reference photos yet. Add a few clear, front-facing ones.",
    "準確度": "Accuracy",
    "越低越寬鬆,搵到更多但可能有錯。": "Lower is looser: finds more, with more mistakes.",
    "寬鬆": "Loose",
    "搵到更多,但可能有錯": "Finds more, but with more mistakes",
    "平衡": "Balanced",
    "建議": "Recommended",
    "嚴格": "Strict",
    "更準確,但可能漏咗啲": "More precise, may miss a few",
    "確認": "Confirm",
    "分數去到呢個百分比就自動當係佢": "Photos at or above this score are counted as a match automatically",
    "待確認": "Review",
    "分數喺呢度同「確認」之間嘅相,留俾你睇": "Photos between this and \"Confirm\" are left for you to review",
    "結果放邊": "Save results to",
    "每次搜尋喺入面開新資料夾": "Each search gets its own folder inside",
    "選擇…": "Browse…",
    "開啟": "Open",
    "結果資料夾:{d}\n再撳「開始搜尋」會繼續放入呢個資料夾;想開新資料夾請撳「新搜尋」。":
        "Results folder: {d}\nStarting again continues in this folder; click \"New search\" for a new one.",
    "未開始。撳「開始搜尋」會喺輸出資料夾入面開一個新資料夾。注意:每次搜尋都會重新複製符合嘅相,會用多啲磁碟空間。":
        "Not started. \"Start search\" creates a new folder inside the output folder. "
        "Note: every search copies its matches again and uses more disk space.",
    # --- tabs, toolbar
    "確認 {n}": "Confirmed {n}",
    "待你確認 {n}": "To review {n}",
    "已排除 {n}": "Excluded {n}",
    "搜尋歷史": "History",
    "縮圖大小": "Thumbnail size",
    "匯出最終結果": "Export final",
    "將確認嘅相複製到結果資料夾嘅 final 入面": "Copies the confirmed photos into the \"final\" folder of this search",
    "更多": "More",
    "重新整理": "Refresh",
    "複製結果": "Copy results",
    "匯出無法檢查清單": "Export unchecked list",
    # --- selection bar
    "已選 {n} 張": "{n} selected",
    "係佢": "It's them",
    "唔係佢": "Not them",
    "清除標記": "Clear mark",
    "取消選取": "Deselect",
    "完成一次搜尋之後先可以標記": "Available after a search has been run",
    # --- status and messages
    "只讀取原相,只複製到輸出資料夾。": "Originals are only read; copies go to the output folder only.",
    "未命名": "Untitled",
    "新搜尋:加入參考相同相片資料夾,再撳「開始搜尋」。":
        "New search: add reference photos and photo folders, then click \"Start search\".",
    "移除呢個搜尋紀錄?\n\n只係移除紀錄,唔會刪除結果資料夾同任何相片。":
        "Remove this search from the history?\n\nOnly the record is removed; the results folder and all photos are kept.",
    "揀相片資料夾(會包括子資料夾)": "Choose a photo folder (sub-folders included)",
    "揀輸出資料夾(唔可以喺相片資料夾入面)": "Choose the output folder (not inside a photo folder)",
    "揀參考相": "Choose reference photos",
    "相片": "Photos",
    "正在分析參考相…": "Analysing reference photos…",
    "參考相已更新。": "Reference photos updated.",
    "從參考相移除呢張?\n{p}\n\n只係由參考相清單移除,唔會刪除相片檔案。":
        "Remove this photo from the references?\n{p}\n\nOnly the reference list changes; the photo file is never deleted.",
    "已移除一張參考相。": "Removed one reference photo.",
    "請先揀一個搜尋。": "Please select a search first.",
    "請先喺結果入面揀相。": "Please select photos in the results first.",
    "{n} 張冇揾到人臉": "{n} had no face",
    "略過 {n} 張": "{n} skipped",
    "清除所有參考相?(已掃描嘅資料唔受影響)": "Clear all reference photos? (Already scanned data is not affected.)",
    "請先撳一個頭像,揀要移除嘅參考相。": "Click an avatar first to choose which reference to remove.",
    "已加入 {n} 個資料夾": "Added {n} folder(s)",
    "掃描前請先加入參考相。": "Please add reference photos before searching.",
    "請先加入並剔選至少一個相片資料夾。": "Please add and tick at least one photo folder.",
    "搵唔到結果資料夾(可能已被搬走):\n{d}": "Results folder not found (it may have been moved):\n{d}",
    "載入人臉模型失敗:{e}": "Could not load the face model: {e}",
    "出錯:": "Error: ",
    "正在停止…": "Stopping…",
    "仍然喺度停止中,請稍後再關閉。": "Still stopping – please close again in a moment.",
    # --- review
    "已確認 {n} 張係佢": "Confirmed {n} as a match",
    "已排除 {n} 張,可以喺「已排除」睇返": "Excluded {n}; you can find them in \"Excluded\"",
    "已清除 {n} 張嘅標記": "Cleared the mark on {n}",
    # --- scan
    "搜尋中…": "Searching…",
    "掃描中…結果放入:{d}": "Scanning… results go to: {d}",
    "正在列出相片…": "Listing photos…",
    "搜尋完成": "Search complete",
    "已停止": "Stopped",
    "磁碟空間不足,已停止": "Stopped: disk space low",
    "輸出磁碟剩餘空間不足,已停止。": "Stopped: the output disk is running low on space. ",
    "已停止。": "Stopped. ",
    "完成:共 {total} 張,新掃描 {scanned},跳過 {skipped},失敗 {failed};已複製 {copied}。":
        "Done: {total} photos, {scanned} newly scanned, {skipped} skipped, {failed} failed; copied {copied}.",
    "{a} 張確認 + {b} 張待你確認": "{a} confirmed + {b} to review",
    "先複製已掃描過嘅 {n} 張符合嘅相…": "First copying {n} matches from photos already scanned…",
    "掃描新相…可以隨時停止,下次會由停低嗰度繼續。": "Scanning new photos… you can stop at any time and continue later.",
    "列出相片中…": "Listing…",
    "{r} 張/秒": "{r} photos/s",
    "已處理": "Processed",
    "速度": "Speed",
    "尚餘時間": "Time left",
    "搵到": "Found",
    "少過 1 分鐘": "under 1 min",
    "約 {m} 分鐘": "about {m} min",
    "約 {h} 小時 {m} 分": "about {h} h {m} min",
    "放開以加入\n資料夾 → 相片資料夾 · 相片 → 參考相": "Drop to add\nfolders → photo folders · photos → references",
    # --- copy / export
    "冇結果可以複製。": "There are no results to copy.",
    "複製完成 {c};記錄:{log}": "Copy finished {c}; log: {log}",
    "複製完成": "Copy finished",
    "請先完成一次搜尋,再匯出最終結果。": "Run a search first, then export the final result.",
    "冇確認嘅相可以匯出。": "There are no confirmed photos to export.",
    "會將 {n} 張確認相複製到\n{d}\\。待確認嘅 {m} 張同已排除嘅唔會包括。原相唔會改動。":
        "{n} confirmed photos will be copied to\n{d}\\\nThe {m} photos to review and the excluded ones are not "
        "included. Your originals are never changed.",
    "匯出完成 {c};記錄:{log}": "Export finished {c}; log: {log}",
    "匯出完成": "Export finished",
    "已匯出 {n} 張到 final 資料夾": "Exported {n} photos to the final folder",
    "匯出完成。要開啟 final 資料夾嗎?": "Export finished. Open the final folder?",
    "冇無法檢查嘅相。": "There are no unchecked photos.",
    "已匯出 {n} 張:{log}": "Exported {n}: {log}",
    "已匯出無法檢查清單": "Unchecked list exported",
    # --- viewer
    "檢視": "Viewer",
    "臉框": "Face box",
    "喺檔案總管顯示": "Show in Explorer",
    "上一張": "Previous",
    "下一張": "Next",
    "唔係佢  N": "Not them  N",
    "係佢  Y": "It's them  Y",
    "顯示 / 隱藏臉框 (F)": "Show / hide face box (F)",
    "開啟相片所在資料夾(只係開啟,唔會改動)": "Open the photo's folder (opening only, nothing changes)",
    "唔係要搵嘅人:由結果移走(檔案唔會刪除)": "Not the person: removed from the results (the file is never deleted)",
    "確認係要搵嘅人": "Confirm this is the person",
    "讀取失敗:{e}": "Could not read the photo: {e}",
    "✓ 已確認係佢": "✓ Confirmed",
    "✗ 已標記唔係佢": "✗ Marked as not them",
    "拍攝日期": "Date taken",
    # --- sort, menu, about
    "相似度": "Similarity",
    "最相似嘅排最前": "Most similar first",
    "最新拍攝嘅排最前(讀取相片嘅 EXIF 日期,冇就用檔案日期)":
        "Newest first (uses the photo's EXIF date, or the file date if it has none)",
    "檢查更新": "Check for updates",
    "關於 Photo Finder Pro": "About Photo Finder Pro",
    "版本 {v}": "Version {v}",
    "100% 離線運作:程式本身唔會連線上網,冇追蹤,冇上載。":
        "100% offline: the app itself never connects to the internet. No tracking, no uploads.",
    "MIT 授權 · 免費開源": "MIT licence · free and open source",
    "喺瀏覽器開啟專案網頁": "Open the project page in your browser",
    "第三方授權聲明": "Third-party notices",
    "開啟 THIRD_PARTY_NOTICES.txt": "Open THIRD_PARTY_NOTICES.txt",
    "關閉": "Close",
}


def set_lang(lang):
    global _lang
    _lang = lang if lang in LANGS else "zh"


def lang():
    return _lang


def tr(text, **kw):
    s = EN.get(text, text) if _lang == "en" else text
    return s.format(**kw) if kw else s
