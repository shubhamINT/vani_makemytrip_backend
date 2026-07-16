# Frontend guide — MakeMyTrip AI Travel Concierge

How the browser connects, talks, and renders travel data from the LiveKit agent.
This describes the app as built in `src/app/`.

## Flow

```
1. user asks (hero)     → first message is buffered
2. POST /token          → backend mints a token + dispatches the agent
3. connect to LiveKit   → using {url, token}
4. send buffered ask    → on connect, the first message is sent
5. converse             → voice + text; agent greets, answers
6. agent shows results  → openui-lang STREAMED on topic "ui.render" → <Renderer> builds live
7. user books           → "Book" button → action sent back to the agent as a chat message
```

Stack: `livekit-client`, `@livekit/components-react`, `@openuidev/react-lang`, `@openuidev/react-ui`.

---

## 1. Token

`POST {VITE_TOKEN_ENDPOINT}` with:
```json
{ "agent_name": "Vani-makemytrip", "id": "optional-user-id" }
```
Response (envelope; `parseTokenResponse` in `useToken.ts` also accepts flat shapes):
```json
{ "success": true, "data": { "token": "eyJ...", "url": "wss://your-livekit-host", "room": "..." } }
```

## 2. Connect + converse

Handled by `Concierge.tsx` via `<LiveKitRoom>` from `@livekit/components-react`
(audio on, video off). `Composer.tsx` toggles the mic and sends typed text with
`useChat().send()`. `Conversation.tsx` merges typed chat + voice transcriptions +
rendered UI into one time-ordered feed.

## 3. Chat vs rendered UI — kept visually separate

The feed has exactly two entry kinds (`Conversation.tsx`, the `Entry` union):

- **`message`** — plain text (typed or transcribed). Renders as a light chat bubble
  (user right, agent left). No card chrome.
- **`ui-render`** — openui-lang streamed on `ui.render`. Renders as a full-width
  **boarding-pass result panel** (labeled "Trip results", collapsible/dismissible)
  via `<Renderer library={openuiChatLibrary}>`. One entry per stream (keyed by
  stream id), updated in place as chunks arrive.

This split is the mechanism that stops "hi / hello" from looking like a hotel card.
Do not merge the two.

## 4. Rendering results — topic `ui.render` (STREAMED)

The agent writes openui-lang line-by-line as a dedicated LLM generates it. Read
incrementally and re-render each chunk — do NOT `reader.readAll()` (that blocks
until the stream ends and kills the live build).

```tsx
room.registerTextStreamHandler("ui.render", async (reader) => {
  let text = "";
  for await (const chunk of reader) {           // openui-lang is streaming-first
    text += chunk;
    upsertUiRenderEntry(reader.info.id, text, true);   // isStreaming
  }
  upsertUiRenderEntry(reader.info.id, text, false);    // stream closed
});
```

`upsertUiRenderEntry(id, text, isStreaming)` updates the entry in place (keyed by
`reader.info.id`) and passes `isStreaming` through:

```tsx
<Renderer response={text} library={openuiChatLibrary} isStreaming={isStreaming} />
```

While `isStreaming` is true, unresolved forward-refs / partial statements are
expected — `<Renderer>` builds progressively. On stream close it flips false so
final parse errors surface. No custom render functions needed — `openuiChatLibrary`
covers cards, tables, charts, images, carousels, lists, callouts, steps, forms,
buttons, follow-ups, etc.

## 5. Booking round-trip — `onAction`

`<Renderer onAction={...}>` fires when the user clicks an interactive element in a
rendered card. `Conversation.tsx` handles it:

- `type === "open_url"` → opens `params.url` in a new tab.
- otherwise (e.g. `@ToAssistant`, `continue_conversation`) → sends
  `event.humanFriendlyMessage` back to the agent via `useChat().send()`.

So a "Book" button becomes a normal chat message to the agent (arrives on `lk.chat`),
which the agent handles to confirm/complete the booking.

## Notes

- **No persistence.** `ui.render` + transcripts are realtime only. Store server-side for history.
- **One room = one session.** Auto-deletes on disconnect. "New search" resets to the hero.
- **Errors.** Token/dispatch failure surfaces a banner + "Start over". Handle `502` on the endpoint.
