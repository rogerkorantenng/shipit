// Create context menu on install
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: 'send-to-shipit',
    title: 'Send to ShipIt',
    contexts: ['selection'],
  })
})

// Handle context menu click
chrome.contextMenus.onClicked.addListener((info) => {
  if (info.menuItemId === 'send-to-shipit' && info.selectionText) {
    // Store selected text for the popup to read
    chrome.storage.local.set({ selectedText: info.selectionText })
    // Show badge to indicate text is ready
    chrome.action.setBadgeText({ text: '!' })
    chrome.action.setBadgeBackgroundColor({ color: '#4F46E5' })
  }
})
