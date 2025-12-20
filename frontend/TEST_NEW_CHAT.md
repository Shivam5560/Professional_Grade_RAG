# Testing New Chat Functionality

## What Was Fixed

1. **Added sessionId to component state** - Now exposed from useChat hook
2. **Added key prop to MessageList** - Forces remount when sessionId changes
3. **Reordered state updates** - sessionId first, then messages
4. **Added comprehensive logging** - Track state changes in real-time

## Testing Steps

1. Open the frontend in browser
2. Send a few messages to create chat history
3. Open browser console (F12)
4. Click "New Chat" button
5. Check console logs for:
   ```
   [ChatInterface] New Chat clicked
   [ChatInterface] Current sessionId: <old-uuid>
   [ChatInterface] Current messages count: X
   [useChat] Clearing chat for session: <old-uuid>
   [useChat] New session created: <new-uuid>
   [useChat] State cleared successfully
   [ChatInterface] State updated: { sessionId: <new-uuid>, messageCount: 0 }
   ```
6. Verify UI shows:
   - Messages cleared
   - Green success alert appears
   - "How can I help you today?" welcome message

## What the Key Prop Does

```tsx
<MessageList
  key={sessionId}  // Forces React to unmount and remount when sessionId changes
  messages={messages}
  isLoading={isLoading}
  latestSources={latestSources}
/>
```

When `sessionId` changes:
1. React sees the key has changed
2. Destroys the old MessageList component instance
3. Creates a brand new MessageList component
4. All internal state (refs, effects) reset
5. Component re-renders with empty messages array

## Expected Console Output

### When clicking New Chat:
```
[ChatInterface] New Chat clicked
[ChatInterface] Current sessionId: "abc-123-old"
[ChatInterface] Current messages count: 5
[useChat] Clearing chat for session: "abc-123-old"
Backend: DELETE /api/v1/chat/history/abc-123-old → 204
[useChat] New session created: "xyz-789-new"
[useChat] State cleared successfully
[ChatInterface] Clear complete - component should re-render
[ChatInterface] State updated: { 
  sessionId: "xyz-789-new", 
  messageCount: 0, 
  messages: [] 
}
```

## If It Still Doesn't Work

Check these potential issues:

1. **Stale Closure**: The `clearChat` callback might be capturing old state
   - Solution: Verify `sessionId` is in dependency array

2. **React Strict Mode**: In development, React may render twice
   - Solution: This is normal, ignore duplicate logs

3. **Browser Cache**: Old bundle might be cached
   - Solution: Hard refresh (Cmd+Shift+R on Mac, Ctrl+Shift+R on Windows)

4. **State Updates Not Batching**: Multiple setState calls
   - Solution: Already reordered to batch properly

5. **Component Not Re-rendering**: Parent component issue
   - Solution: Key prop forces remount

## Debugging Commands

```bash
# Clear Next.js cache
cd frontend
rm -rf .next
npm run dev

# Check if changes are compiled
grep -n "key={sessionId}" components/chat/ChatInterface.tsx
```

## Files Modified

- `frontend/hooks/useChat.ts` - Added sessionId state management
- `frontend/components/chat/ChatInterface.tsx` - Added key prop and logging
