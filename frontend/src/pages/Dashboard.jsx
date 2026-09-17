import { useEffect, useState } from "react";
import Header from "../components/Header";
import SummaryCard from "../components/SummaryCard";
import TaskList from "../components/TaskList";
import MeetingList from "../components/MeetingList";
import FollowUpList from "../components/FollowUpList";
import UnresolvedList from "../components/UnresolvedList";
import ChatWindow from "../components/ChatWindow";
import LoadingState from "../components/LoadingState";
import { getCompletedTasks, getDashboard, getDeadlines, getFollowUps, getMeetings, getOpenTasks, getSummary, getUnresolved } from "../services/api";

export default function Dashboard() {
  const [dashboard, setDashboard] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  async function loadDashboard() {
    setLoading(true);
    setError("");
    try {
      const [summary, openTasks, completedTasks, meetings, deadlines, followUps, unresolved, aggregate] = await Promise.all([
        getSummary(), getOpenTasks(), getCompletedTasks(), getMeetings(), getDeadlines(), getFollowUps(), getUnresolved(), getDashboard(),
      ]);
      setDashboard({
        as_of: summary.as_of,
        summary,
        open_tasks: openTasks.tasks,
        completed_tasks: completedTasks.tasks,
        meetings: meetings.meetings,
        upcoming_deadlines: deadlines.upcoming_deadlines,
        overdue_or_at_risk_items: deadlines.overdue_or_at_risk_items,
        follow_ups: followUps.follow_ups,
        unresolved_items: unresolved.unresolved_items,
        waiting_on_others: aggregate.waiting_on_others,
        others_waiting_on_arjun: aggregate.others_waiting_on_arjun,
      });
    } catch (reason) {
      setError(reason.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { loadDashboard(); }, []);

  const deadlineItems = dashboard
    ? [...new Map([...dashboard.upcoming_deadlines, ...dashboard.overdue_or_at_risk_items].map((item) => [item.id, item])).values()]
    : [];

  if (error) return <main className="app-shell"><div className="error-state"><p className="eyebrow">Executive Productivity Agent</p><h1>Dashboard unavailable</h1><p>{error} Confirm the FastAPI service is running, then refresh this page.</p><button type="button" onClick={loadDashboard}>Retry connection</button></div></main>;
  if (loading || !dashboard) return <main className="app-shell"><LoadingState label="Loading your executive view" /></main>;

  return <main className="app-shell"><Header asOf={dashboard.as_of} /><div className="dashboard-content"><div className="summary-grid"><SummaryCard label="Open tasks" value={dashboard.summary.open_task_count} note="Needs attention" tone="blue" /><SummaryCard label="Upcoming meetings" value={dashboard.meetings.length} note="On your calendar" tone="mint" /><SummaryCard label="Follow-ups" value={dashboard.follow_ups.length} note="Keep moving" tone="amber" /><SummaryCard label="Unresolved items" value={dashboard.summary.unresolved_item_count} note="Needs clarity" tone="rose" /></div><div className="main-grid"><div className="overview-column"><section className="overview"><p className="eyebrow">Today at a glance</p><h2>Keep the important work moving.</h2><p>Your view is grounded in the latest known tasks, calendar entries, conversations, and voice notes. Start with what needs your decision.</p><div className="overview-stats"><div><strong>{dashboard.overdue_or_at_risk_items.length}</strong><span>At risk</span></div><div><strong>{dashboard.waiting_on_others.length}</strong><span>Waiting on others</span></div><div><strong>{dashboard.others_waiting_on_arjun.length}</strong><span>Waiting on you</span></div></div></section><div className="two-column"><FollowUpList items={dashboard.others_waiting_on_arjun} title="Waiting on me" /><FollowUpList items={dashboard.waiting_on_others} title="I'm waiting on" /></div><UnresolvedList items={dashboard.unresolved_items} /></div><MeetingList items={dashboard.meetings} /></div><TaskList items={dashboard.open_tasks} title="Open tasks" /><TaskList items={dashboard.completed_tasks} title="Completed tasks" /><TaskList items={deadlineItems} title="Deadlines" /><ChatWindow /></div></main>;
}