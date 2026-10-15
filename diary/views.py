from django.shortcuts import render, redirect
from django.utils.crypto import get_random_string
from datetime import date, timedelta
from collections import Counter
import time

def home(request):
    entries = request.session.get("entries", {})
    today = date.today().isoformat()

    # Статистика
    count = len(entries)
    streak = 0
    sorted_dates = sorted(entries.keys(), reverse=True)

    prev_date = None
    for d in sorted_dates:
        if streak == 0:
            streak += 1
            prev_date = d
        else:
            # Проверяем, что даты идут подряд
            current_date_obj = date.fromisoformat(d)
            expected_prev = (current_date_obj + timedelta(days=1)).isoformat()
            if expected_prev == prev_date:
                streak += 1
                prev_date = d
            else:
                break

    if count > 0:
        moods = [entries[d]["mood"] for d in sorted_dates]
        most_common_mood, _ = Counter(moods).most_common(1)[0]
    else:
        most_common_mood = None

    # Прогноз настроения на завтра
    forecast_mood = "🌙" 
    if count > 0:
        moods = [entries[d]["mood"] for d in sorted_dates[:7]]
        good_count = moods.count("very_good") + moods.count("good")
        bad_count = moods.count("bad") + moods.count("very_bad")
        normal_count = moods.count("normal")

        if good_count > bad_count and good_count > normal_count:
            forecast_mood = "😄 Завтра будет хороший день!"
        elif bad_count > good_count and bad_count > normal_count:
            forecast_mood = "😔 Завтра может быть непросто, но ты справишься!"
        else:
            forecast_mood = "🌤 Завтра будет обычный день."

    # Токен для «поделиться»
    share_token = request.session.get("share_token")
    share_url = None
    if share_token:
        share_url = f"/share/{share_token}/"

    context = {
        "week_list": [(d, entries[d]) for d in sorted_dates[:7]],
        "count": count,
        "streak": streak,
        "most_common_mood": most_common_mood,
        "forecast_mood": forecast_mood,
        "share_url": share_url,
        "dark_theme": request.session.get("dark_theme", False),
    }
    return render(request, "diary/home.html", context)

def save_entry(request):
    if request.method != "POST":
        return redirect("home")

    today = date.today().isoformat()
    mood = request.POST.get("mood")
    note = request.POST.get("note", "")[:140]

    # Лимит: не больше 5 сохранений в минуту
    timestamps = request.session.get("save_timestamps", [])
    now_ts = int(time.time())

    timestamps = [ts for ts in timestamps if now_ts - ts < 60]
    if len(timestamps) >= 5:
        request.session["message"] = "Слишком часто сохраняете: не более 5 раз в минуту."
        return redirect("home")

    timestamps.append(now_ts)
    request.session["save_timestamps"] = timestamps

    entries = request.session.get("entries", {})
    entries[today] = {"mood": mood, "note": note}

    # Оставляем только последние 7 дней
    sorted_dates = sorted(entries.keys(), reverse=True)
    if len(sorted_dates) > 7:
        for d in sorted_dates[7:]:
            del entries[d]

    request.session["entries"] = entries
    request.session.pop("message", None)
    return redirect("home")

def reset_entries(request):
    if request.method == "POST":
        request.session.pop("entries", None)
        request.session.pop("save_timestamps", None)
    return redirect("home")

def toggle_theme(request):
    if request.method != "POST":
        return redirect("home")
    current = request.session.get("dark_theme", False)
    request.session["dark_theme"] = not current
    return redirect("home")

def generate_share_token(request):
    if request.method != "POST":
        return redirect("home")

    token = get_random_string(length=8)
    expire_ts = int(time.time()) + 3600
    request.session["share_token"] = token
    request.session["share_expire"] = expire_ts
    return redirect("home")

def share_view(request, token):
    stored_token = request.session.get("share_token")
    expire = request.session.get("share_expire")

    now = int(time.time())
    is_valid = stored_token == token and expire and now < expire

    if not is_valid:
        context = {"error": "Ссылка истекла или неверна."}
        return render(request, "diary/share.html", context)

    entries = request.session.get("entries", {})
    sorted_dates = sorted(entries.keys(), reverse=True)
    recent = [(d, entries[d]) for d in sorted_dates[:7]]

    context = {
        "recent": recent,
        "token": token,
        "dark_theme": request.session.get("dark_theme", False),
    }
    return render(request, "diary/share.html", context)
