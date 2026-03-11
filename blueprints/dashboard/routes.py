from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import WeeklyRow, VisionItem, Setting, JournalEntry, Habit, HabitLog, SavedTip, FocusSession
from datetime import datetime
import random

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    weekly_data = WeeklyRow.query.filter_by(user_id=current_user.id).order_by(WeeklyRow.week.asc()).all()
    vision_items = VisionItem.query.filter_by(user_id=current_user.id).order_by(VisionItem.sort_order).all()

    # Fetch settings
    user_settings_raw = Setting.query.filter_by(user_id=current_user.id).all()
    settings = {s.key: s.value for s in user_settings_raw}
    
    # Fetch habits and today's logs
    habits = Habit.query.filter_by(user_id=current_user.id).all()
    today = datetime.utcnow().date()
    
    habit_statuses = {}
    for h in habits:
        log = HabitLog.query.filter_by(habit_id=h.id, date=today).first()
        habit_statuses[h.id] = log.status if log else False

    # Fetch journal entries
    journals = JournalEntry.query.filter_by(user_id=current_user.id).order_by(JournalEntry.created_at.desc()).limit(5).all()

    # Focus Sessions today
    focus_today = FocusSession.query.filter(FocusSession.user_id == current_user.id, FocusSession.completed_at >= today).all()
    total_focus_minutes = sum(f.duration for f in focus_today)

    # Calculate average completion for weekly data
    avg_completion = 0
    recent_improvement = 0
    if len(weekly_data) >= 1:
        current_week = weekly_data[-1]
        c_score = (current_week.health + current_week.career + current_week.finance + current_week.personal) / 4
        avg_completion = round(c_score, 2)
        
        if len(weekly_data) >= 2:
            prev_week = weekly_data[-2]
            p_score = (prev_week.health + prev_week.career + prev_week.finance + prev_week.personal) / 4
            recent_improvement = round(c_score - p_score, 1)

    # Micro-learning feature
    learning_tips = [
        "Use the 2-minute rule: If a task takes less than 2 minutes, do it now.",
        "Monotasking is 40% more productive than multitasking.",
        "Take a 5-minute break every 25 minutes using the Pomodoro technique.",
        "Your brain is for having ideas, not holding them. Write everything down.",
        "Review your goals every morning to stay aligned with your purpose.",
        "Focus on 'Highest Leverage Activities' first in your day.",
        "Sleep is the ultimate productivity hack; aim for 7-9 hours."
    ]
    daily_tip = random.choice(learning_tips)

    # Fetch saved tips
    saved_tips = SavedTip.query.filter_by(user_id=current_user.id).order_by(SavedTip.saved_at.desc()).all()

    return render_template('index.html', 
                           weekly_data=weekly_data, 
                           vision_items=vision_items, 
                           avg_completion=avg_completion,
                           recent_improvement=recent_improvement,
                           settings=settings,
                           habits=habits,
                           habit_statuses=habit_statuses,
                           journals=journals,
                           daily_tip=daily_tip,
                           saved_tips=saved_tips,
                           total_focus_minutes=total_focus_minutes)

@dashboard_bp.route('/log_focus', methods=['POST'])
@login_required
def log_focus():
    duration = request.form.get('duration', type=int)
    category = request.form.get('category', default='Deep Work')
    if not duration:
        return jsonify({"success": False, "message": "No duration found."}), 400
        
    session = FocusSession(duration=duration, category=category, user_id=current_user.id)
    db.session.add(session)
    db.session.commit()
    return jsonify({"success": True, "total_today": sum(f.duration for f in FocusSession.query.filter(FocusSession.user_id == current_user.id, FocusSession.completed_at >= datetime.utcnow().date()).all())})

@dashboard_bp.route('/guide')
@login_required
def guide():
    return render_template('welcome.html')

@dashboard_bp.route('/add_week', methods=['POST'])
@login_required
def add_week():
    week = request.form.get('week', type=int)
    health = request.form.get('health', type=int)
    career = request.form.get('career', type=int)
    finance = request.form.get('finance', type=int)
    personal = request.form.get('personal', type=int)
    
    if WeeklyRow.query.filter_by(user_id=current_user.id, week=week).first():
        flash(f'Week {week} already exists.', 'warning')
        return redirect(url_for('dashboard.index'))
    
    new_row = WeeklyRow(
        week=week,
        health=health,
        career=career,
        finance=finance,
        personal=personal,
        user_id=current_user.id
    )
    db.session.add(new_row)
    db.session.commit()
    flash('Weekly row added successfully!', 'success')
    return redirect(url_for('dashboard.index'))

@dashboard_bp.route('/edit_week', methods=['POST'])
@login_required
def edit_week():
    week_id = request.form.get('week_id', type=int)
    row = WeeklyRow.query.get_or_404(week_id)
    
    if row.user_id != current_user.id:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    row.health = request.form.get('health', type=int)
    row.career = request.form.get('career', type=int)
    row.finance = request.form.get('finance', type=int)
    row.personal = request.form.get('personal', type=int)
    
    db.session.commit()
    flash(f'Week {row.week} updated.', 'success')
    return redirect(url_for('dashboard.index'))

@dashboard_bp.route('/delete_week/<int:week_id>', methods=['POST'])
@login_required
def delete_week(week_id):
    row = WeeklyRow.query.get_or_404(week_id)
    if row.user_id != current_user.id:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    db.session.delete(row)
    db.session.commit()
    flash('Weekly row deleted.', 'info')
    return redirect(url_for('dashboard.index'))

@dashboard_bp.route('/add_journal', methods=['POST'])
@login_required
def add_journal():
    title = request.form.get('title')
    content = request.form.get('content')
    if not content:
        flash('Journal content cannot be empty.', 'warning')
        return redirect(url_for('dashboard.index'))
    
    entry = JournalEntry(title=title, content=content, user_id=current_user.id)
    db.session.add(entry)
    db.session.commit()
    flash('Journal entry saved.', 'success')
    return redirect(url_for('dashboard.index'))

@dashboard_bp.route('/toggle_habit/<int:habit_id>')
@login_required
def toggle_habit(habit_id):
    habit = Habit.query.get_or_404(habit_id)
    if habit.user_id != current_user.id:
        return jsonify({"error": "unauthorized"}), 403
    
    today = datetime.utcnow().date()
    log = HabitLog.query.filter_by(habit_id=habit.id, date=today).first()
    
    if log:
        log.status = not log.status
    else:
        log = HabitLog(habit_id=habit.id, date=today, status=True)
        db.session.add(log)
    
    db.session.commit()
    return redirect(url_for('dashboard.index'))

@dashboard_bp.route('/save_tip', methods=['POST'])
@login_required
def save_tip():
    tip_content = request.form.get('tip_content')
    if not tip_content:
        flash('No tip to save.', 'warning')
        return redirect(url_for('dashboard.index'))
    
    # Check if already saved
    existing = SavedTip.query.filter_by(user_id=current_user.id, content=tip_content).first()
    if existing:
        flash('Tip already in your library.', 'info')
        return redirect(url_for('dashboard.index'))
    
    saved_tip = SavedTip(content=tip_content, user_id=current_user.id)
    db.session.add(saved_tip)
    db.session.commit()
    flash('Tip saved to your library!', 'success')
    return redirect(url_for('dashboard.index'))

@dashboard_bp.route('/delete_saved_tip/<int:tip_id>', methods=['POST'])
@login_required
def delete_saved_tip(tip_id):
    tip = SavedTip.query.get_or_404(tip_id)
    if tip.user_id != current_user.id:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    db.session.delete(tip)
    db.session.commit()
    flash('Tip removed from library.', 'info')
    return redirect(url_for('dashboard.index'))

@dashboard_bp.route('/update_settings', methods=['POST'])
@login_required
def update_settings():
    for key, value in request.form.items():
        if key == 'csrf_token':
            continue
        setting = Setting.query.filter_by(user_id=current_user.id, key=key).first()
        if not setting:
            setting = Setting(user_id=current_user.id, key=key)
            db.session.add(setting)
        setting.value = value
    db.session.commit()
    flash('Settings updated.', 'success')
    return redirect(url_for('dashboard.index'))

@dashboard_bp.route('/add_vision', methods=['POST'])
@login_required
def add_vision():
    img = request.form.get('img')
    quote = request.form.get('quote')
    category = request.form.get('category')
    
    new_item = VisionItem(
        img=img,
        quote=quote,
        category=category,
        user_id=current_user.id
    )
    db.session.add(new_item)
    db.session.commit()
    flash('Vision item added!', 'success')
    return redirect(url_for('dashboard.index'))

@dashboard_bp.route('/delete_vision/<int:item_id>', methods=['POST'])
@login_required
def delete_vision(item_id):
    item = VisionItem.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    db.session.delete(item)
    db.session.commit()
    flash('Vision item removed.', 'info')
    return redirect(url_for('dashboard.index'))
