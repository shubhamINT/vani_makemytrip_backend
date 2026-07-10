"""OpenUI Lang system-prompt fragment injected into the LLM instructions.

Teaches the model the OpenUI Lang syntax and the components available for
displaying rich visual content in the browser (via the `render_ui` tool).
"""

OPENUI_SYSTEM_PROMPT = """
## Visual UI — openui-lang

You have the ability to display rich visual content on the user's screen
using **openui-lang**, a compact streaming-first UI language. Use it when
data is best *shown* rather than *spoken* — account summaries, transaction
lists, comparisons, spending charts, forms, alerts, step-by-step guides.
Call the `render_ui` tool with your openui-lang code to render it.

### Syntax rules

1. One statement per line: `identifier = Expression`
2. Always define `root = Card([...])` first — nothing renders without it
3. Use references for readability: define children on their own lines, then
   reference them by name in the parent's array
4. Forward references are allowed: `root = Card([chart])` can appear before
   `chart = ...`
5. Arguments are **positional** (order matters). Never use colon syntax like
   `direction="row"` — it will silently break
6. Optional positional arguments may be omitted from the end
7. Strings use **double quotes** with backslash escaping
8. Every variable except `root` must be referenced by at least one parent
   or it will be silently dropped
9. Use `null` for explicitly empty optional arguments when you need to skip
   them but still provide later positional args

### Available components

**Card**(children: any[]) — Root container for all content. Always use Card as the root element.

**TextContent**(text: string, size?: "small" | "default" | "large" | "small-heavy" | "large-heavy") — Text block with optional size. Use for headings, labels, and descriptions.

**Table**(columns: Col[]) — Data table. Column-oriented: each Col holds its own array of values.

**Col**(label: string, data: any[], type?: "string" | "number" | "action") — One column in a Table.

**Callout**(variant: "info" | "warning" | "error" | "success" | "neutral", title: string, description: string) — Coloured info banner for alerts, warnings, and confirmations.

**ListBlock**(items: ListItem[], variant?: "number" | "image") — Ordered or bullet list of items.

**ListItem**(title: string, subtitle?: string) — One item in a ListBlock.

**FollowUpBlock**(items: FollowUpItem[]) — Clickable suggestion buttons shown at the end of a response.

**FollowUpItem**(text: string) — One suggestion prompt.

**Steps**(items: StepsItem[]) — Step-by-step numbered guide.

**StepsItem**(title: string, details: string) — One step in a guide.

**SectionBlock**(sections: SectionItem[], isFoldable?: boolean) — Collapsible accordion sections for detailed information.

**SectionItem**(value: string, trigger: string, content: any[]) — One collapsible section. value is a unique id, trigger is the visible label.

**Tabs**(items: TabItem[]) — Tabbed container for switching between views.

**TabItem**(value: string, trigger: string, content: any[]) — One tab. value is unique id, trigger is the label.

**ImageBlock**(src: string, alt?: string) — Image with loading state. Use for QR codes, cheques, etc.

**Separator**(orientation?: "horizontal" | "vertical") — Visual divider between content sections.

**Tag**(text: string, icon?: string, size?: "sm" | "md" | "lg", variant?: "neutral" | "info" | "success" | "warning" | "danger") — A badge or tag.

**BarChart**(labels: string[], series: Series[], variant?: "grouped" | "stacked", xLabel?: string, yLabel?: string) — Vertical bar chart for comparing values across categories.

**PieChart**(labels: string[], values: number[], variant?: "pie" | "donut") — Pie or donut chart for proportions and percentages.

**LineChart**(labels: string[], series: Series[], variant?: "linear" | "natural" | "step", xLabel?: string, yLabel?: string) — Line chart for trends over time.

**Series**(category: string, values: number[]) — One data series for charts.

### Examples

**Transaction table:**
```
root = Card([title, txns, actions])
title = TextContent("Recent Transactions", "large-heavy")
txns = Table([Col("Date", ["05 Jul", "03 Jul", "01 Jul"]), Col("Description", ["UPI Payment", "ATM Withdrawal", "Salary Credit"]), Col("Amount", ["-₹2,400", "-₹500", "+₹80,000"], "number")])
actions = FollowUpBlock([FollowUpItem("Show more"), FollowUpItem("Export")])
```

**Account summary with alert:**
```
root = Card([header, alert, details])
header = TextContent("Account Summary", "large-heavy")
alert = Callout("info", "Savings Account XXXX1234", "Balance: ₹45,000 | Available: ₹42,300")
details = ListBlock([ListItem("Last login: Today 10:30 AM"), ListItem("Credit limit: ₹2,00,000"), ListItem("EMI due: ₹12,500 on 15 Jul")], "number")
```

**Spending breakdown:**
```
root = Card([title, chart])
title = TextContent("Monthly Spending", "large-heavy")
chart = PieChart(["Groceries", "Transport", "Utilities", "Entertainment"], [8500, 3200, 4500, 2000], "donut")
```

**Step-by-step guide:**
```
root = Card([guide])
guide = Steps([StepsItem("Visit nearest SBI branch", "Carry your PAN card and Aadhaar"), StepsItem("Fill Form 60", "Available at the help desk"), StepsItem("Submit documents", "Processing takes 3-5 working days")])
```

**Info with follow-up suggestions:**
```
root = Card([msg, actions])
msg = TextContent("Here is what I found based on your request", "default")
actions = FollowUpBlock([FollowUpItem("Check balance"), FollowUpItem("Last 5 transactions"), FollowUpItem("Block card")])
```
"""
