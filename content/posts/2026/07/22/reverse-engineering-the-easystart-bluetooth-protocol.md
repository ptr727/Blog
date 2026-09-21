---
title: Reverse Engineering the EasyStart Bluetooth Protocol
date: '2026-07-22T12:00:00+00:00'
url: /2026/07/22/reverse-engineering-the-easystart-bluetooth-protocol/
categories:
- solution
- homeautomation
tags:
- esphome
- bluetooth
- homeassistant
- hvac
- reverse-engineering
- claude
---
I have two [Micro-Air EasyStart](https://www.microair.net/products/easystart-flex-home-ac-soft-starter) soft starters, one on each HVAC compressor, fitted in 2023. They exist because a compressor starting on a hot afternoon used to pull enough inrush current to brown out the house, and my server UPSs would notice before I did. A soft starter ramps the motor instead of slamming it, and the brownouts stopped.

The modules have a Bluetooth radio and a phone app that shows live current, line frequency, and a start counter. I wanted those numbers in Home Assistant. Micro-Air would not share the protocol, I could not find anyone who had decoded it, and I gave up on it for about two years.

This post is about picking it back up, decoding the protocol out of the vendor's own Android app, and what happened when the result promptly started rebooting my ESP32.

## The app already has the protocol in it

The thing I had been missing is that a Bluetooth device's protocol is rarely secret. It is compiled into the app that talks to it, and an Android app is a zip file full of bytecode that decompiles cleanly.

The whole first phase is three commands and no hardware:

```sh
# a. pull the app off a phone with USB debugging on
adb shell pm list packages | grep -i easystart
adb shell pm path net.microair.easystart
adb pull /data/app/.../base.apk net.microair.easystart-4.2-19.apk

# b. unpack it two ways, because they are good at different things
apktool d net.microair.easystart-4.2-19.apk -o app-apktool   # smali, closer to the truth
jadx     net.microair.easystart-4.2-19.apk -d app-jadx       # Java, easier to read

# c. then just grep
grep -rn "0000180[0-9a-f]\|[0-9a-f]\{8\}-[0-9a-f]\{4\}-" app-apktool/smali | sort -u
grep -rn "writeCharacteristic\|onCharacteristicChanged\|setValue" app-apktool/smali
```

The version matters and is worth putting in the filename. I decoded `net.microair.easystart` 4.2, version code 19, and a future reader deserves to know whether they are looking at the same app I was.

Three classes had everything. `Connect` does the connection and the service discovery. `MainActivityKt$gattCallBack$1` is the GATT callback, which is where the response framing lives. `Status` polls on a timer and parses the frame, and it carries the fault-code table as a plain array of strings. **No hardware was involved in any of this.** I had the transport, the command, and the byte layout before I went anywhere near a compressor.

## What the app said, including one thing that is a trap

The transport is a Laird BLE module exposing the Laird VSP service, which tunnels a byte stream over GATT:

```text
service d973f2e0-b19e-11e2-9e96-0800200c9a66
  d973f2e1-...  notify   module -> host, carries the responses
  d973f2e2-...  write    host -> module, carries the commands
```

**`e1` is notify and `e2` is write, which is the reverse of the usual Laird convention.** I had read enough about VSP to "know" which way round it went, and I was wrong. I confirmed the real roles by opening the GATT table once in nRF Connect on my phone and reading the properties off the two characteristics. That is the only thing I used a phone app for in the whole project.

There is no pairing, no bonding, no PIN, no passkey, and no application handshake. I am claiming that from absence, which is normally weak evidence, but the decompiled app contains no `createBond`, no `setPin`, no `passkey`, and no auth strings at all. There is nothing there to call.

Commands are ASCII strings written to `e2`. They look like JSON and are not:

```text
{"Cmd": ReadLive}
{"Cmd": ReadEEP}
{"Cmd": NormMode}
{"Cmd": ProgMode}
```

The value is unquoted and there is a space after the colon. Feeding that to a JSON encoder produces something the module ignores, so the bytes go out as a literal string. Only `ReadLive` matters for monitoring. The OTA and flash-buffer commands are in there too, and I left them alone: I wanted to read this thing, not brick it.

## Eighteen bytes, and no checksum anywhere

Each `ReadLive` produces **two** notifications, which is the framing detail that cost me the most time later. One is an 18-byte binary frame. The other is an ASCII `{"Sts": Success}` acknowledgment. They arrive in that order and a host has to handle both.

The frame, little-endian and unsigned throughout:

```text
10 00 00 05 3f 00 a9 20 f5 00 00 00 00 00 53 13 00 00
```

| Offset | Field | Formula | This frame |
| --- | --- | --- | --- |
| `[0]` | header | constant `0x10` | 16 |
| `[1]` | reserved | always zero | 0 |
| `[2]` | system state | table below | 0, Normal |
| `[3]` | learned starts | raw | 5 |
| `[4..5]` | **live current** | `u16 / 10` A | 6.3 A |
| `[6..7]` | **line frequency** | `500000 / u16` Hz | 59.8 Hz |
| `[8..9]` | last start peak | `u16 / 10` A | 24.5 A |
| `[10..11]` | short-cycle delay | raw u16 | 0 |
| `[12..13]` | total faults | raw u16 | 0 |
| `[14..17]` | **total starts** | u32 | 4947 |

Two of those are not guessable from staring at bytes.

**Line frequency is a period, not a scaled reading.** The field holds 8361, and 8361 is not 59.8 in any scaling. It is `500000 / 8361 = 59.80`. I would have burned a long time trying to fit a multiplier to that if the app had not shown me the division.

**Total starts is 32 bits**, spanning four bytes where every other multi-byte field uses two. A 16-bit read looks completely fine until the counter passes 65535, which on a compressor is a few years out, and then it silently wraps.

The state byte is a lookup into an array the app carries:

| Code | Meaning |
| --- | --- |
| 0 | Normal |
| 1 | Unexpctd Curr Flt |
| 2 | Short Cycle Delay |
| 3 | Pwr Intrrptn Fault |
| 4 | Stall Fault |
| 5 | Stuck SR Fault |
| 6 | Open Ovrld Fault |
| 7 | Overcurrent Fault |
| 8 | Bad Wiring Fault |
| 9 | Wrong Voltage Flt |

Code 2 is worth knowing. It is a transient waiting state after a stop, not a fault, and treating it as one gives you an alert every cycle.

**There is no checksum and no CRC in the frame.** I went looking for one, because you expect one, and the two unexplained bytes at `[0]` and `[1]` look exactly like where it would live. `[0]` is a constant `0x10` and `[1]` is always zero, in every frame I have captured. Neither is needed to decode anything.

## The phone is the wrong tool for capture

Having the layout is not the same as having it right, so the decode needed a real capture. Two approaches failed first, and both fail in a way that looks like success.

**nRF Connect on a phone only shows you the latest value of a characteristic.** Both notifications land on the same characteristic, and the ASCII ack arrives second, so the app faithfully displayed `{"Sts": Success}` and the binary frame was simply never on screen. I spent a while believing the module answered a poll with a status string and nothing else.

**Android's HCI snoop log is useless on a stock phone.** Turning on "Enable Bluetooth HCI snoop log" produces a log, and you feel like you are getting somewhere. On a stock Pixel it runs in `FILTERED` mode, and the `btsnooz_hci.log` inside a bugreport keeps only the first few bytes of each ATT payload. It confirmed the handles and that the write payload started `7b 22 43`, which is `{"C`, and it gave me a frame-length estimate of about 20 bytes that turned out to be wrong. The real frame is 18. Unfiltered capture needs root.

What worked was the boring option: use the laptop as the Bluetooth central. A short [bleak](https://bleak.readthedocs.io/) script, run with `uv` so there is no virtualenv to set up, connects, polls, and prints every notification raw with a per-byte index alongside the decoded interpretation:

```sh
uv run easystart_monitor.py --discover
uv run easystart_monitor.py --name EasyStart_XXXX
```

Printing the raw bytes next to the decode is the part that matters. When a field is wrong you can see which byte moved.

One constraint that shapes everything: **only one BLE central can be connected at a time.** The phone app has to be closed before the laptop can connect, which also means you cannot watch the app and the capture side by side.

## Ground truth is the vendor's own screen

The decode is only worth anything if it agrees with the instrument that already works. So: connect the phone app, read the numbers off it, close it, connect the monitor, read its numbers.

| Field | App | Decode |
| --- | --- | --- |
| Live current | 6.6 A | 6.3 A on the frame taken seconds later |
| Last start peak | 24.5 A | 24.5 A |
| Line frequency | 59.8 Hz | 59.8 Hz |
| Total starts | 4947 | 4947 |
| System state | Normal | 0 |

Peak, frequency, and the counter match exactly, which is what pins the scaling and the endianness. Live current is a live value and moves between the two readings, so agreeing to a few tenths is the most that measurement can prove.

## The radio is the sensor

Then a behavior I did not design for and would not have predicted.

**The module powers its Bluetooth radio only while the compressor is running.** When the compressor stops, the module stops advertising and drops the connection. There is no idle state to poll.

That sounds like a limitation and it is actually the single most useful thing I learned. **The presence of the BLE connection is a reliable compressor-running signal**, more reliable than any threshold I would have picked on the current reading. The `running` sensor in my integration is driven by the GATT connection state, not by comparing current against some number I made up.

It does have one consequence worth stating plainly: **there is no such thing as a standby current reading here.** Every sample is a running sample, so the `/10` scaling is validated against running values only, and I have no evidence about what the field would do at rest because the field does not exist at rest.

When a compressor stops, `running` goes off, the live sensors publish NaN so Home Assistant shows `unknown` rather than a stale number, and the cumulative counters keep their last value, because there is nothing fresher to show and a counter reading zero would be a lie.

## Then I found the same decode, twice

After it was all working, I went looking again and found two people had been here before me: [Keen-coffee](https://github.com/Keen-coffee/home_assistant/blob/main/easyStart) did the original work, and [DerekSeaman](https://github.com/DerekSeaman/ESPHome-Micro-Air-EasyStart) built on it.

My decode matches theirs byte for byte. The swapped characteristics, the two-notification framing, the `500000 / period` frequency, the 32-bit counter, all of it. Independently arriving at the same answer is about as good as verification gets for something with no specification.

I will not pretend that was the plan. Searching harder in 2023 would have saved me the whole exercise. What my version adds is byte `[3]`, the learned-starts value, which neither of theirs decodes, and it builds the sensors through ESPHome's Python code generation rather than through YAML lambdas.

## Getting it into Home Assistant

The integration is an ESPHome external component: a `ble_client` node that polls `ReadLive` on an interval, parses the frame, and publishes current, an estimated power, line frequency, last start peak, short-cycle delay, system state, the running flag, and the three counters.

**The power figure is an estimate and the sensor says so.** The module reports single-leg current and no voltage at all, so power is `current * line_voltage * power_factor` with defaults of 240 V and 1.0. It is useful for spotting a change. It is not a meter.

Four things cost me real time on the hardware side.

**Range is much worse than you expect.** These radios are weak. My existing Bluetooth proxy, in the office, would not hold a connection at all. The eventual answer was a dedicated ESP32 with an external antenna, physically sited at the units outside.

That diagnosis was guesswork until I added a signal-strength sensor, using ESPHome's built-in `ble_client` RSSI type. It reads the RSSI of the live connection rather than of advertisements, which matters here because a module stops advertising once something is connected to it. The office proxy measured **-93 dBm** on a live link, which is essentially the sensitivity floor. Around -60 dBm is healthy. That one number turned "everything is intermittently unavailable" into "the radio is too far away", which is a fixable problem.

**Connection slots are finite and the accounting is not obvious.** An active `bluetooth_proxy` reserves three, so a proxy hosting two modules needs `esp32_ble: max_connections: 5`. The RSSI sensor attaches to an existing client and costs nothing extra.

**Changing that number needs a clean rebuild.** `max_connections` maps to a compile-time sdkconfig value. An incremental build regenerates the C++ and keeps the cached config, so the change appears to apply and does nothing at runtime. `esphome clean` first, then verify the value in the generated sdkconfig rather than trusting the build.

**`esphome upload` does not compile.** After a failed build it will cheerfully flash the previous binary, which is a genuinely confusing way to spend twenty minutes wondering why your change did not take effect.

## The part that rebooted my ESP32

With the component deployed, the device started rebooting. Not always, and not predictably. Sometimes instead of rebooting it would connect, report itself subscribed, and then simply never receive a notification.

Two symptoms, same firmware, same peer, no pattern I could see:

```text
[12:17:50][D][ble_client:056]: All clients established, services released
[12:17:50]assert failed: list_end list.c:272 (list != NULL)
[12:17:50]rst:0xc (RTC_SW_CPU_RST),boot:0x2b (SPI_FAST_FLASH_BOOT)
```

```text
[11:49:40][D][ble_client:056]: All clients established, services released
[11:49:40][W][esp32_ble_client:224]: [0] esp_ble_gattc_get_descr_by_char_handle error, status=10
```

Status 10 is `ESP_GATT_NOT_FOUND`. The CCCD never gets written, so no notification ever arrives, while the node believes it is subscribed. That is the worse of the two, because a reboot at least announces itself.

I left a device capturing serial for eighty minutes. In that window there were **five service releases and five races: four silent, one panic.** Only the consequence varied. The ordering was wrong every single time.

The cause turned out to be in ESPHome itself, and it takes three things happening together:

1. `ble_client` releases the peer's discovered services **inside the same event dispatch** that told the nodes about the event, as soon as every node reports `ESTABLISHED`.
2. That release calls `esp_ble_gattc_cache_clean()`, which frees **Bluedroid's** GATT database, not just ESPHome's copy of it.
3. `esp_ble_gattc_register_for_notify()` is asynchronous. A node that reports `ESTABLISHED` while its own registration is still in flight lets the release run first, and when the registration event finally arrives, the handler walks a database that has been freed.

Bluedroid then either returns `ESP_GATT_NOT_FOUND` or asserts on the freed list and aborts the chip. Same bug, two outcomes, and which one you get is timing.

The reason this is not a famous bug is the genuinely interesting part. Several of the stock `ble_client` automation nodes register themselves and then **never report `ESTABLISHED` at all**. That pins the "all nodes established" test false forever, which suppresses the release entirely, which hides the crash and leaks the memory the release existed to reclaim. **A single `ble_client.disconnect` action anywhere in a configuration is enough to hide this.** Keen-coffee's implementation of the same hardware is protected twice over by exactly that accident, and pays the leak instead.

So I wrote a reproduction: about sixty lines carrying no protocol knowledge, whose only job is to report `ESTABLISHED` one line too early, driven by a config that forces reconnects with a `lambda` rather than the disconnect action, because the action would have masked the very thing under test.

Then I filed it, with the capture, the decoded backtrace, and the reduced case: [esphome/esphome#17921](https://github.com/esphome/esphome/issues/17921). Two fixes went with it. [#17919](https://github.com/esphome/esphome/pull/17919) holds the release while a registration is outstanding and guards the lookup, and it merged on 30 July, shipping in 2026.8.0. [#17920](https://github.com/esphome/esphome/pull/17920) fixes the nodes that never report established, and was deliberately held in draft until the first had landed, because restoring the release would otherwise have re-exposed those configurations to the crash. It merged on 8 September and shipped in 2026.9.0.

My own component is fixed by moving one line: it reports `ESTABLISHED` inside the registration event, after checking that the registration actually succeeded, instead of four lines earlier. That was always the correct thing to do. It is still a workaround, and worth saying so plainly, because obeying an unwritten rule is not the same as the rule being enforced, and the penalty for not knowing it was a reboot.

## I did almost none of this by hand

Like the [blog migration](/2026/08/01/moving-this-blog-from-wordpress-to-hugo/), I ran this through [Claude Code](https://claude.com/claude-code), and the shape of it is worth describing because it is not what I expected.

I did not hand it the problem and wait. I did a step manually, from what I had learned watching [Matt Brown's reverse engineering videos](https://www.youtube.com/@mattbrwn), then asked it to automate that step, then did the next step manually, then automated that. Pull the APK, automate it. Decompile and grep, automate it. Decode a field, generalize the decoder. Each round I also asked it to write up what we had just done, and refine the write-up with whatever had actually gone wrong, which is how the gotchas in this post came to be written down at all rather than forgotten.

At the end I deleted every artifact I had made by hand and gave it one prompt:

> I have the Micro-Air EasyStart app installed on my Android phone, developer options and USB debugging are on, and it's plugged into this computer. Extract the APK, decompile it, and reverse-engineer its Bluetooth protocol. Then write me a `uv`-runnable `bleak` monitor to validate the decode against the live module. And finally write an ESPHome `ble_client` component to expose it to Home Assistant.

It drove the whole thing: `adb`, `apktool`, `jadx`, the grepping, the byte layout, the monitor, the component. My entire contribution was plugging in the phone, tapping one USB debugging prompt, standing near a compressor, running one command, and pasting text back.

That is the part I would emphasize to anyone thinking about this kind of project. **The barrier to reverse engineering a device was never the difficulty. It was the tedium**, and the tedium is the part that is now cheap. The judgment still has to come from somewhere: deciding the swapped characteristics needed confirming against real hardware rather than assuming the convention, deciding that an 80-minute capture was the evidence the upstream issue needed, deciding not to touch the OTA commands. But the ratio of what I decided to what I would have had to type is not close.

## Was it worth it

For the telemetry, honestly, marginally. I now have compressor current and start counts on a dashboard, and I look at them rarely.

For everything else, yes. I have a repeatable method written down, I found a real defect in a widely deployed project and it is fixed upstream for everyone, and I learned that the thing I had assumed was hard was mostly just slow.

The method generalized, which was the point of writing it down. The next target is a Goodnature A24 rat trap, which is a much smaller problem: the community reckons it broadcasts its kill count in the advertisement, so if that still holds it needs no connection and no APK at all. Capture the advertisement first, and only reach for the decompiler if that comes up empty.

The protocol, the ESPHome component, the monitor, and the full byte-level documentation are [on GitHub](https://github.com/ptr727/ESPHome-Config/tree/main/easystart). If you want to discuss any of it, the repo has Discussions enabled, which is also why this post has no comment box below it.
