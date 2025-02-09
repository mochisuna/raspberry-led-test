import RPi.GPIO as GPIO
import time
import threading

# GPIOピン設定
LED_PINS = {"red": 17, "green": 27, "blue": 22}
SWITCH_PINS = {"red": 14, "green": 15, "blue": 18, "all": 4}
DEBOUNCE_TIME = 0.2  # 200ms デバウンス
FLICKERING_TIME = 0.17

# 各LEDのモード（0:消灯, 1:常時点灯, 2:点滅）
led_modes = {"red": 0, "green": 0, "blue": 0}

# GPIO設定
GPIO.setmode(GPIO.BCM)
for pin in LED_PINS.values():
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)

for pin in SWITCH_PINS.values():
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# スイッチの状態管理
last_press_time = {"red": 0, "green": 0, "blue": 0, "all": 0}


# 点滅用スレッド
def led_blink():
    while True:
        for color, mode in led_modes.items():
            if mode == 2:  # 点滅モード
                GPIO.output(LED_PINS[color], GPIO.HIGH)
            time.sleep(FLICKERING_TIME)  # 約3回/秒
            if mode == 2:
                GPIO.output(LED_PINS[color], GPIO.LOW)
        time.sleep(FLICKERING_TIME)


# LED のモード切り替え関数
def toggle_led_mode(color):
    global led_modes
    led_modes[color] = (led_modes[color] + 1) % len(led_modes)  # 0 → 1 → 2 → 0
    print(f"{color} LED Mode: {led_modes[color]}")
    apply_led_state()


# LEDの状態を適用
def apply_led_state():
    for color, mode in led_modes.items():
        if mode == 0:
            GPIO.output(LED_PINS[color], GPIO.LOW)
        elif mode == 1:
            GPIO.output(LED_PINS[color], GPIO.HIGH)


# 一括点灯処理
def all_led_on():
    global led_modes
    mode = 1
    for color in led_modes.keys():
        if led_modes[color] == 1:
            mode = 0
        else:
            mode = 1
            break
    for color in led_modes.keys():
        led_modes[color] = mode
    apply_led_state()
    print(f"All LEDs set to Mode {mode}")


# スイッチ監視
def check_switches():
    while True:
        for color, pin in LED_PINS.items():
            if GPIO.input(SWITCH_PINS[color]) == GPIO.LOW:  # スイッチが押された
                if time.time() - last_press_time[color] > DEBOUNCE_TIME:
                    toggle_led_mode(color)
                    last_press_time[color] = time.time()

        if GPIO.input(SWITCH_PINS["all"]) == GPIO.LOW:  # 一括点灯スイッチ
            if time.time() - last_press_time["all"] > DEBOUNCE_TIME:
                all_led_on()
                last_press_time["all"] = time.time()

        time.sleep(0.05)  # 負荷軽減のため小休止


# スレッド実行
threading.Thread(target=led_blink, daemon=True).start()
threading.Thread(target=check_switches, daemon=True).start()

try:
    while True:
        time.sleep(1)  # メインループは特に処理せず待機
except KeyboardInterrupt:
    print("終了")
    GPIO.cleanup()
