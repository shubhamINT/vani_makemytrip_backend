# Frontend guide — connecting to the SBI voice agent

How the browser connects, talks, and renders data from the LiveKit voice agent.

## Flow

```
1. POST /token          → your backend mints a token + dispatches the agent
2. connect to LiveKit   → using {url, token} from step 1
3. enable mic           → user speaks; agent hears
4. agent joins + greets → you hear audio, see transcript
5. agent sends data     → openui-lang on topic "ui.render" → OpenUI `<Renderer>` parses + renders it
```

Install: `npm i livekit-client @openuidev/react-lang @openuidev/react-ui`

---

## 1. Get a token

`POST /token` on your backend.

Request:
```json
{ "agent_name": "voice-agent", "id": "optional-user-id" }
```
- `agent_name` (required) — used for room naming + persona. Use `"voice-agent"`.
- `id` (optional) — a customer id; if set, the backend looks the user up and gives
  the agent their context. Omit for an anonymous caller.

Response (standard envelope):
```json
{
  "success": true,
  "message": "token created",
  "data": { "token": "eyJ...", "url": "wss://your-livekit-host", "room": "voice-agent-web-ab12cd" }
}
```
Use `data.url` and `data.token` to connect. Token TTL is 30 min.

---

## 2. Connect + talk

```ts
import { Room, RoomEvent, Track } from "livekit-client";

const res = await fetch("/token", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ agent_name: "voice-agent" }),
});
const { data } = await res.json();

const room = new Room();

// Play the agent's voice
room.on(RoomEvent.TrackSubscribed, (track) => {
  if (track.kind === Track.Kind.Audio) {
    const el = track.attach();
    document.body.appendChild(el); // hidden <audio>, autoplays
  }
});

await room.connect(data.url, data.token);
await room.localParticipant.setMicrophoneEnabled(true); // start talking
```

That's it — the agent is already dispatched into the room and greets first. The
user speaks; barge-in is on (talk over the agent and it stops).

---

## 3. What to expect

- **Agent greets first** — a short spoken greeting right after it joins.
- **Turn-taking is automatic** — the agent detects when the user stops and replies.
  Short "uh-huh" won't cut it off; real speech interrupts instantly.
- **Text input is allowed too** — send typed messages instead of / alongside voice:
  ```ts
  await room.localParticipant.sendText("show my last 3 transactions", { topic: "lk.chat" });
  ```
- **Agent state** (optional UI: thinking/speaking indicator):
  ```ts
  room.on(RoomEvent.ParticipantAttributesChanged, () => {/* read agent state */});
  ```
  Or use the prebuilt `@livekit/components-react` hooks if you're on React.

---

## 4. Live transcript

Transcription flows on LiveKit's **reserved** `lk.transcription` topic. Do **not**
send your own data on it. Register a handler to show captions:

```ts
room.registerTextStreamHandler("lk.transcription", async (reader, info) => {
  for await (const chunk of reader) {
    // append chunk to the transcript bubble for info.identity
  }
});
```
On React, the `@livekit/components-react` chat/transcript components do this for you.

---

## 5. Custom UI data — topic `ui.render` (OpenUI Lang)

When the agent decides data is better *shown* than *spoken*, it calls the
`render_ui` function tool, which pushes **raw openui-lang text** on the
**`ui.render`** topic (separate from the transcript). The frontend feeds this
text into OpenUI's `<Renderer>` component, which parses and renders it
automatically.

### Install

```bash
npm i livekit-client @openuidev/react-lang @openuidev/react-ui
```

### Wire the handler

Replace the old JSON `switch` handler with this:

```tsx
import { Renderer } from "@openuidev/react-lang";
import { openuiChatLibrary } from "@openuidev/react-ui";
import "@openuidev/react-ui/components.css";
import "@openuidev/react-ui/styles/index.css";

function AgentUI() {
  const [response, setResponse] = useState<string | null>(null);

  useEffect(() => {
    room.registerTextStreamHandler("ui.render", async (reader) => {
      const text = await reader.readAll();
      setResponse(text);
    });
  }, []);

  if (!response) return null;

  return (
    <Renderer
      response={response}
      library={openuiChatLibrary}
      onError={(errors) => console.error("OpenUI render error:", errors)}
    />
  );
}
```

> The agent also *says* a short line ("check the display") when it sends UI,
> so the user knows to look.

### What you'll receive

The agent sends **raw openui-lang** — a line-oriented markup language. Here are
examples of what the LLM may generate:

**Table of transactions:**
```text
root = Card([title, txns])
title = TextContent("Recent Transactions", "large-heavy")
txns = Table([Col("Date", ["05 Jul", "03 Jul"]), Col("Description", ["UPI Payment", "Salary Credit"]), Col("Amount", ["-₹1,200", "+₹80,000"], "number")])
```

**Account summary with info alert:**
```text
root = Card([header, alert, details])
header = TextContent("Account Summary", "large-heavy")
alert = Callout("info", "Savings Account XXXX1234", "Balance: ₹45,000")
details = ListBlock([ListItem("Last login: Today 10:30 AM"), ListItem("EMI due: ₹12,500")], "number")
```

**Spending donut chart:**
```text
root = Card([title, chart])
title = TextContent("Monthly Spending", "large-heavy")
chart = PieChart(["Groceries", "Transport", "Utilities"], [8500, 3200, 4500], "donut")
```

**Step-by-step guide:**
```text
root = Card([guide])
guide = Steps([StepsItem("Visit nearest SBI branch", "Carry your PAN card and Aadhaar"), StepsItem("Fill Form 60", "Available at the help desk")])
```

**Follow-up suggestions:**
```text
root = Card([msg, actions])
msg = TextContent("Here is what I found", "default")
actions = FollowUpBlock([FollowUpItem("Check balance"), FollowUpItem("Show transactions"), FollowUpItem("Block card")])
```

### OpenUI rendering is handled for you

You do **not** need to write custom render functions. OpenUI's `<Renderer>`
accepts the raw openui-lang text and a `library` prop, then parses the text and
renders the matching React components. The built-in `openuiChatLibrary`
includes all the components the agent is taught to use (tables, cards, charts,
lists, callouts, follow-up buttons, steps, tabs, accordions, and more).

If you need to customise the visual theme, wrap the renderer in OpenUI's
`<ThemeProvider>` or use the `createTheme` API. See
[docs at openui.com](https://www.openui.com) for theming details.

---

## Notes

- **No persistence.** `ui.render` and transcripts are realtime only — a client that
  joins late misses earlier packets. Store server-side if you need history.
- **One room = one call.** The room auto-deletes when the participant disconnects.
- **Errors:** `POST /token` returns `502` if agent dispatch fails; handle it and
  retry / show a "try again" state.
