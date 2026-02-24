#!/usr/bin/env python3
"""
Meeting Notes to Tasks
Extract action items from meeting notes.
Creates structured task list with assignees and deadlines.
"""

import json
import os
import re
from datetime import datetime, timedelta

TASKS_DIR = os.path.expanduser("~/.openclaw/workspace/skills/stream2/2025-02-24-1834-meeting-tasks")
TASKS_FILE = os.path.join(TASKS_DIR, "tasks.json")

def ensure_dir():
    if not os.path.exists(TASKS_DIR):
        os.makedirs(TASKS_DIR)

def load_tasks():
    if os.path.exists(TASKS_FILE):
        with open(TASKS_FILE) as f:
            return json.load(f)
    return {"tasks": [], "meetings": []}

def save_tasks(data):
    with open(TASKS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def extract_tasks_from_notes(notes_text):
    """Extract action items from meeting notes"""
    tasks = []
    
    lines = notes_text.split('\n')
    
    # Patterns for action items
    patterns = [
        r'^[-*]\s*(.+?)(?:\s*@(\w+))?(?:\s*#(\d+[hdwm]))?$',  # - Task @assignee #deadline
        r'^(?:TODO|ACTION|TASK):?\s*(.+?)(?:\s*@(\w+))?(?:\s*#(\d+[hdwm]))?$',  # TODO: Task
        r'^(\w+)\s+ wird\s+(.+?)(?:\s*#(\d+[hdwm]))?$',  # Max wird etwas machen
    ]
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        for pattern in patterns:
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                task_text = match.group(1).strip()
                assignee = match.group(2) if len(match.groups()) > 1 and match.group(2) else None
                deadline_str = match.group(3) if len(match.groups()) > 2 and match.group(3) else None
                
                # Parse deadline
                deadline = None
                if deadline_str:
                    deadline = parse_deadline(deadline_str)
                
                tasks.append({
                    'text': task_text,
                    'assignee': assignee,
                    'deadline': deadline,
                    'raw_line': line,
                    'status': 'open',
                    'created_at': datetime.now().isoformat()
                })
                break
    
    return tasks

def parse_deadline(deadline_str):
    """Parse deadline like 2d, 1w, 3h into date"""
    try:
        value = int(deadline_str[:-1])
        unit = deadline_str[-1]
        
        if unit == 'h':
            delta = timedelta(hours=value)
        elif unit == 'd':
            delta = timedelta(days=value)
        elif unit == 'w':
            delta = timedelta(weeks=value)
        elif unit == 'm':
            delta = timedelta(days=value * 30)
        else:
            return None
        
        return (datetime.now() + delta).strftime('%Y-%m-%d')
    except:
        return None

def process_meeting_notes(meeting_title, notes_text, date=None):
    """Process meeting notes and extract tasks"""
    ensure_dir()
    
    if not date:
        date = datetime.now().strftime('%Y-%m-%d')
    
    # Extract tasks
    tasks = extract_tasks_from_notes(notes_text)
    
    # Create meeting record
    meeting = {
        'id': datetime.now().strftime('%Y%m%d_%H%M%S'),
        'title': meeting_title,
        'date': date,
        'notes': notes_text,
        'tasks_extracted': len(tasks),
        'created_at': datetime.now().isoformat()
    }
    
    # Add meeting ID to tasks
    for task in tasks:
        task['meeting_id'] = meeting['id']
        task['meeting_title'] = meeting_title
    
    # Save
    data = load_tasks()
    data['meetings'].append(meeting)
    data['tasks'].extend(tasks)
    save_tasks(data)
    
    return meeting, tasks

def list_tasks(status=None, assignee=None):
    """List tasks with filters"""
    data = load_tasks()
    tasks = data['tasks']
    
    if status:
        tasks = [t for t in tasks if t['status'] == status]
    if assignee:
        tasks = [t for t in tasks if t.get('assignee') == assignee]
    
    return tasks

def format_task(task):
    """Format task for display"""
    emoji = {
        'open': '⬜',
        'done': '✅',
        'in_progress': '🔄'
    }.get(task['status'], '⬜')
    
    assignee = f" @{task['assignee']}" if task.get('assignee') else ""
    deadline = f" (📅 {task['deadline']})" if task.get('deadline') else ""
    
    return f"{emoji} {task['text']}{assignee}{deadline}"

def generate_summary():
    """Generate task summary"""
    data = load_tasks()
    tasks = data['tasks']
    
    open_tasks = [t for t in tasks if t['status'] == 'open']
    done_tasks = [t for t in tasks if t['status'] == 'done']
    
    # Group by assignee
    by_assignee = {}
    for task in open_tasks:
        assignee = task.get('assignee') or 'Unassigned'
        if assignee not in by_assignee:
            by_assignee[assignee] = []
        by_assignee[assignee].append(task)
    
    summary = f"📊 *TASK SUMMARY*\n\n"
    summary += f"⬜ Open: {len(open_tasks)}\n"
    summary += f"✅ Done: {len(done_tasks)}\n"
    summary += f"📊 Total: {len(tasks)}\n\n"
    
    for assignee, tasks_list in by_assignee.items():
        summary += f"👤 *{assignee}* ({len(tasks_list)})\n"
        for task in tasks_list:
            deadline = f" 📅{task['deadline']}" if task.get('deadline') else ""
            summary += f"  ⬜ {task['text'][:40]}{deadline}\n"
        summary += "\n"
    
    return summary

def export_to_markdown():
    """Export all tasks to markdown"""
    data = load_tasks()
    tasks = data['tasks']
    
    md_file = os.path.join(TASKS_DIR, "tasks_export.md")
    
    with open(md_file, 'w') as f:
        f.write("# Meeting Tasks\n\n")
        f.write(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n")
        
        # Open tasks
        f.write("## ⬜ Open Tasks\n\n")
        for task in tasks:
            if task['status'] == 'open':
                f.write(format_task(task) + "\n")
        
        # Done tasks
        f.write("\n## ✅ Completed Tasks\n\n")
        for task in tasks:
            if task['status'] == 'done':
                f.write(format_task(task) + "\n")
    
    return md_file

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Meeting Notes to Tasks')
    parser.add_argument('action', choices=['process', 'list', 'summary', 'export'])
    parser.add_argument('--title', '-t', help='Meeting title')
    parser.add_argument('--file', '-f', help='Notes file')
    parser.add_argument('--notes', '-n', help='Notes text')
    parser.add_argument('--status', '-s', choices=['open', 'done', 'in_progress'])
    parser.add_argument('--assignee', '-a', help='Filter by assignee')
    
    args = parser.parse_args()
    
    if args.action == 'process':
        notes = args.notes
        if args.file:
            with open(args.file) as f:
                notes = f.read()
        
        if notes and args.title:
            meeting, tasks = process_meeting_notes(args.title, notes)
            print(f"\n✅ Meeting processed: {meeting['title']}")
            print(f"   Tasks extracted: {len(tasks)}\n")
            for task in tasks:
                print(f"   {format_task(task)}")
        else:
            print("Usage: meeting_tasks.py process --title 'Meeting Name' --notes '...'")
    
    elif args.action == 'list':
        tasks = list_tasks(args.status, args.assignee)
        print(f"\n📋 Tasks ({len(tasks)}):\n")
        for task in tasks:
            print(format_task(task))
    
    elif args.action == 'summary':
        print(generate_summary())
    
    elif args.action == 'export':
        md_file = export_to_markdown()
        print(f"✅ Exported to {md_file}")
    
    else:
        print("📝 Meeting Notes to Tasks")
        print("\nUsage:")
        print("  process --title 'Meeting' --notes '...'")
        print("  list [--status open] [--assignee max]")
        print("  summary")
        print("  export")
