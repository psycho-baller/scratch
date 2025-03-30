#!/usr/bin/swift

import AppKit

func setClipboardHTML(html: String) {
  let pasteboard = NSPasteboard.general
  pasteboard.clearContents()
  let htmlData = Data(html.utf8)
  let htmlType = NSPasteboard.PasteboardType.html
  pasteboard.setData(htmlData, forType: htmlType)
}

// Read full HTML content from stdin
let inputHTML = String(data: FileHandle.standardInput.readDataToEndOfFile(), encoding: .utf8) ?? ""
setClipboardHTML(html: inputHTML)