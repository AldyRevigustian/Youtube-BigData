import streamlit as st
import redis
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config
import uuid


def safe_parse_timestamp(timestamp_str):
    """Safely parse timestamp string, handling microseconds"""
    try:
        # Handle microseconds by truncating to 6 digits if longer
        if "." in timestamp_str and "+" in timestamp_str:
            # Split on timezone
            dt_part, tz_part = timestamp_str.rsplit("+", 1)
            if "." in dt_part:
                dt_base, microsec = dt_part.split(".")
                # Truncate microseconds to 6 digits
                microsec = microsec[:6]
                timestamp_str = f"{dt_base}.{microsec}+{tz_part}"
        elif "." in timestamp_str and timestamp_str.endswith("Z"):
            # Handle Z timezone
            dt_part = timestamp_str[:-1]
            if "." in dt_part:
                dt_base, microsec = dt_part.split(".")
                microsec = microsec[:6]
                timestamp_str = f"{dt_base}.{microsec}Z"
        elif "." in timestamp_str:
            # Handle no timezone
            if "." in timestamp_str:
                dt_base, microsec = timestamp_str.split(".")
                microsec = microsec[:6]
                timestamp_str = f"{dt_base}.{microsec}"

        return datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
    except Exception as e:
        st.error(f"Error parsing timestamp {timestamp_str}: {e}")
        return datetime.now()


# Page configuration
st.set_page_config(
    page_title="YouTube Live Stream Analytics",
    page_icon="📺",
    layout="wide",
    initial_sidebar_state="expanded",
)


class Dashboard:
    def __init__(self):
        # Initialize Redis connection
        self.redis_client = redis.Redis(
            host=config.REDIS_HOST,
            port=config.REDIS_PORT,
            db=config.REDIS_DB,
            decode_responses=True,
        )

    def get_sentiment_counts(self):
        """Get sentiment counts from Redis"""
        try:
            positive = int(
                self.redis_client.get(f"{config.SENTIMENT_CACHE_KEY}:counts:positive")
                or 0
            )
            negative = int(
                self.redis_client.get(f"{config.SENTIMENT_CACHE_KEY}:counts:negative")
                or 0
            )
            neutral = int(
                self.redis_client.get(f"{config.SENTIMENT_CACHE_KEY}:counts:neutral")
                or 0
            )

            return {"positive": positive, "negative": negative, "neutral": neutral}
        except Exception as e:
            st.error(f"Error getting sentiment counts: {e}")
            return {"positive": 0, "negative": 0, "neutral": 0}

    def get_recent_comments(self, limit=20):
        """Get recent comments from Redis"""
        try:
            # Get recent comment IDs from timeline
            comment_ids = self.redis_client.zrevrange(
                f"{config.SENTIMENT_CACHE_KEY}:timeline", 0, limit - 1
            )

            comments = []
            for comment_id in comment_ids:
                comment_data = self.redis_client.get(
                    f"{config.SENTIMENT_CACHE_KEY}:{comment_id}"
                )
                if comment_data:
                    comments.append(json.loads(comment_data))

            return comments
        except Exception as e:
            st.error(f"Error getting recent comments: {e}")
            return []

    def get_latest_summary(self):
        """Get latest comment summary"""
        try:
            summary_data = self.redis_client.get(f"{config.SUMMARY_CACHE_KEY}:latest")
            if summary_data:
                return json.loads(summary_data)
            return None
        except Exception as e:
            st.error(f"Error getting latest summary: {e}")
            return None

    def get_summary_history(self, limit=10):
        """Get summary history"""
        try:
            summary_ids = self.redis_client.zrevrange(
                f"{config.SUMMARY_CACHE_KEY}:timeline", 0, limit - 1
            )

            summaries = []
            for summary_id in summary_ids:
                summary_data = self.redis_client.get(
                    f"{config.SUMMARY_CACHE_KEY}:{summary_id}"
                )
                if summary_data:
                    summaries.append(json.loads(summary_data))

            return summaries
        except Exception as e:
            st.error(f"Error getting summary history: {e}")
            return []

    def render_metrics(self):
        """Render key metrics"""
        sentiment_counts = self.get_sentiment_counts()
        total_comments = sum(sentiment_counts.values())

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Comments", total_comments)

        with col2:
            st.metric(
                "Positive",
                sentiment_counts["positive"],
                delta=(
                    f"{(sentiment_counts['positive']/total_comments*100):.1f}%"
                    if total_comments > 0
                    else "0%"
                ),
            )

        with col3:
            st.metric(
                "Negative",
                sentiment_counts["negative"],
                delta=(
                    f"{(sentiment_counts['negative']/total_comments*100):.1f}%"
                    if total_comments > 0
                    else "0%"
                ),
            )

        with col4:
            st.metric(
                "Neutral",
                sentiment_counts["neutral"],
                delta=(
                    f"{(sentiment_counts['neutral']/total_comments*100):.1f}%"
                    if total_comments > 0
                    else "0%"
                ),
            )

    def render_sentiment_chart(self):
        """Render sentiment distribution chart"""
        sentiment_counts = self.get_sentiment_counts()

        if sum(sentiment_counts.values()) == 0:
            st.info("No sentiment data available yet")
            return

        # Pie chart
        fig = px.pie(
            values=list(sentiment_counts.values()),
            names=list(sentiment_counts.keys()),
            title="Sentiment Distribution",
            color_discrete_map={
                "positive": "#2E8B57",
                "negative": "#DC143C",
                "neutral": "#4682B4",
            },
        )

        fig.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig, use_container_width=True)

    def render_recent_comments(self):
        """Render recent comments table"""
        comments = self.get_recent_comments()

        if not comments:
            st.info("No recent comments available")
            return

        # Create DataFrame
        df = pd.DataFrame(comments)

        # Format data for display
        df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.strftime("%H:%M:%S")
        df["confidence"] = df["confidence"].round(3)

        # Color code by sentiment
        def color_sentiment(val):
            if val == "positive":
                return "background-color: #90EE90"
            elif val == "negative":
                return "background-color: #FFB6C1"
            else:
                return "background-color: #ADD8E6"

        styled_df = df[
            ["timestamp", "username", "comment", "sentiment", "confidence"]
        ].style.applymap(color_sentiment, subset=["sentiment"])

        st.dataframe(styled_df, use_container_width=True)

    def render_latest_summary(self):
        """Render latest comment summary"""
        summary = self.get_latest_summary()

        if not summary:
            st.info("No summary available yet")
            return

        st.subheader("📋 Latest Summary")

        # Summary info
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Time Window", f"{config.SUMMARY_WINDOW_MINUTES} minutes")
            st.metric("Total Comments", summary["total_comments"])
        with col2:
            window_start = safe_parse_timestamp(summary["window_start"]).strftime(
                "%H:%M"
            )
            window_end = safe_parse_timestamp(summary["window_end"]).strftime("%H:%M")
            st.metric("Window", f"{window_start} - {window_end}")

        # Summary text
        # st.text_area("Summary", summary['summary'], height=150, disabled=True, key=f"latest_summary_{summary.get('window_start', datetime.now().isoformat())}")
        st.text_area(
            "Summary",
            summary["summary"],
            height=150,
            disabled=True,
            key=f"latest_summary_{uuid.uuid4()}",
        )

        # Sentiment distribution for this window
        if "sentiment_distribution" in summary:
            st.subheader("Sentiment in This Window")

            sentiment_data = []
            for sentiment, stats in summary["sentiment_distribution"].items():
                sentiment_data.append(
                    {
                        "Sentiment": sentiment.capitalize(),
                        "Count": stats["count"],
                        "Avg Confidence": f"{stats['avg_confidence']:.3f}",
                    }
                )

            if sentiment_data:
                df_sentiment = pd.DataFrame(sentiment_data)
                st.dataframe(df_sentiment, use_container_width=True)

    def render_summary_history(self):
        """Render summary history"""
        summaries = self.get_summary_history()

        if not summaries:
            st.info("No summary history available")
            return

        st.subheader("📚 Summary History")

        for i, summary in enumerate(summaries):
            with st.expander(
                f"Summary {i+1} - {safe_parse_timestamp(summary['timestamp']).strftime('%H:%M:%S')} "
                f"({summary['total_comments']} comments)"
            ):
                unique_key = f"historical_summary_{uuid.uuid4()}"
                st.text_area("Summary", summary['summary'], height=150, disabled=True, key=unique_key)
                # st.text_area(
                #     f"Summary {i+1}",
                #     summary["summary"],
                #     height=100,
                #     disabled=True,
                #     key=f"historical_summary_{i}_{summary.get('timestamp', 'unknown')}",
                # )

def main():
    # Title
    st.title("📺 YouTube Live Stream Analytics")
    st.markdown(f"**Channel:** {config.CHANNEL_NAME} | **Video ID:** {config.VIDEO_ID}")

    # Initialize dashboard
    dashboard = Dashboard()

    # Sidebar
    st.sidebar.title("⚙️ Settings")
    auto_refresh = st.sidebar.checkbox("Auto Refresh", value=True)
    refresh_interval = st.sidebar.slider("Refresh Interval (seconds)", 5, 60, 10)

    # Auto refresh
    if auto_refresh:
        placeholder = st.empty()

        while True:
            with placeholder.container():
                # Key metrics
                st.header("📊 Real-time Metrics")
                dashboard.render_metrics()

                # Charts and data
                col1, col2 = st.columns([1, 2])

                with col1:
                    dashboard.render_sentiment_chart()

                with col2:
                    st.subheader("💬 Recent Comments")
                    dashboard.render_recent_comments()

                # Summary section
                st.header("📋 Comment Summaries")

                tab1, tab2 = st.tabs(["Latest Summary", "Summary History"])

                with tab1:
                    dashboard.render_latest_summary()

                with tab2:
                    dashboard.render_summary_history()

                # Status
                st.sidebar.success(
                    f"Last updated: {datetime.now().strftime('%H:%M:%S')}"
                )

            time.sleep(refresh_interval)
    else:
        # Static render
        dashboard.render_metrics()

        col1, col2 = st.columns([1, 2])

        with col1:
            dashboard.render_sentiment_chart()

        with col2:
            st.subheader("💬 Recent Comments")
            dashboard.render_recent_comments()

        st.header("📋 Comment Summaries")

        tab1, tab2 = st.tabs(["Latest Summary", "Summary History"])

        with tab1:
            dashboard.render_latest_summary()

        with tab2:
            dashboard.render_summary_history()


if __name__ == "__main__":
    main()
