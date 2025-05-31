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
import requests
import pymongo
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import io
from typing import Dict, Any
import subprocess
import psutil
import numpy as np
from collections import Counter
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import seaborn as sns
import re

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config
import uuid


def safe_parse_timestamp(timestamp_str):
    try:
        if not timestamp_str:
            return datetime.now()
        timestamp_str = timestamp_str.strip()
        if "." in timestamp_str:
            if "+" in timestamp_str:
                dt_part, tz_part = timestamp_str.rsplit("+", 1)
                if "." in dt_part:
                    dt_base, microsec = dt_part.split(".", 1)
                    microsec = microsec.ljust(6, "0")[:6]
                    timestamp_str = f"{dt_base}.{microsec}+{tz_part}"
            elif timestamp_str.endswith("Z"):
                dt_part = timestamp_str[:-1]
                if "." in dt_part:
                    dt_base, microsec = dt_part.split(".", 1)
                    microsec = microsec.ljust(6, "0")[:6]
                    timestamp_str = f"{dt_base}.{microsec}Z"
            else:
                dt_base, microsec = timestamp_str.split(".", 1)
                microsec = microsec.ljust(6, "0")[:6]
                timestamp_str = f"{dt_base}.{microsec}"
        timestamp_str = timestamp_str.replace("Z", "+00:00")
        return datetime.fromisoformat(timestamp_str)
    except Exception as e:
        st.warning(
            f"⚠️ Error parsing timestamp '{timestamp_str}': {e}. Using current time."
        )
        return datetime.now()


st.set_page_config(
    page_title="YouTube Live Stream Analytics",
    page_icon="📺",
    layout="wide",
    initial_sidebar_state="expanded",
)


class Dashboard:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=config.REDIS_HOST,
            port=config.REDIS_PORT,
            db=config.REDIS_DB,
            decode_responses=True,
        )
        self.video_info = None

        self.mongo_client = None
        self.mongo_db = None
        self.init_mongodb()

        self.load_data_from_mongodb_to_redis()

    def load_data_from_mongodb_to_redis(self):
        try:
            comments_collection_name = f"{config.VIDEO_ID}_comments"
            comments_collection = self.mongo_db[comments_collection_name]
            total_mongo_comments = comments_collection.count_documents({})

            with st.spinner(
                f"🔄 Loading {total_mongo_comments} existing comments from MongoDB to Redis..."
            ):
                comments = list(comments_collection.find({}).sort("timestamp", 1))

                sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
                loaded_count = 0

                for comment in comments:
                    try:
                        comment_data = {
                            "comment_id": comment.get("id", ""),
                            "username": comment.get("username", ""),
                            "comment": comment.get("comment", ""),
                            "timestamp": comment.get("timestamp", ""),
                            "sentiment": comment.get("sentiment", "neutral"),
                            "confidence": comment.get("confidence", 0.0),
                        }
                        comment_key = (
                            f"{config.SENTIMENT_CACHE_KEY}:{comment_data['comment_id']}"
                        )
                        self.redis_client.set(comment_key, json.dumps(comment_data))

                        timestamp = safe_parse_timestamp(
                            comment_data["timestamp"]
                        ).timestamp()
                        self.redis_client.zadd(
                            f"{config.SENTIMENT_CACHE_KEY}:timeline",
                            {comment_data["comment_id"]: timestamp},
                        )

                        sentiment = comment_data["sentiment"].lower()
                        if sentiment in sentiment_counts:
                            sentiment_counts[sentiment] += 1

                        loaded_count += 1

                    except Exception as e:
                        st.warning(
                            f"⚠️ Error loading comment {comment.get('comment_id', 'unknown')}: {e}"
                        )
                        continue

                for sentiment, count in sentiment_counts.items():
                    if count > 0:
                        self.redis_client.set(
                            f"{config.SENTIMENT_CACHE_KEY}:counts:{sentiment}", count
                        )
        except Exception as e:
            st.error(f"🔴 Error loading data from MongoDB to Redis: {e}")

    def check_process_status(self):
        """Check if system processes are running"""
        processes = {
            "youtube_api": {"status": "🔴", "details": "Not running"},
            "comment_cleaner": {"status": "🔴", "details": "Not running"},
            "sentiment_analyzer": {"status": "🔴", "details": "Not running"},
            "comment_summarizer": {"status": "🔴", "details": "Not running"},
            "streamlit_dashboard": {"status": "🔴", "details": "Not running"},
        }

        try:

            for proc in psutil.process_iter(["pid", "name", "cmdline"]):
                try:
                    cmdline = proc.info["cmdline"]
                    if not cmdline:
                        continue

                    cmdline_str = " ".join(cmdline).lower()

                    if "youtube_api.py" in cmdline_str:
                        processes["youtube_api"] = {
                            "status": "🟢",
                            "details": f"Running  \n(PID: {proc.info['pid']})",
                        }

                    elif "comment_cleaner.py" in cmdline_str:
                        processes["comment_cleaner"] = {
                            "status": "🟢",
                            "details": f"Running  \n(PID: {proc.info['pid']})",
                        }

                    elif "sentiment_analyzer.py" in cmdline_str:
                        processes["sentiment_analyzer"] = {
                            "status": "🟢",
                            "details": f"Running  \n(PID: {proc.info['pid']})",
                        }

                    elif "comment_summarizer.py" in cmdline_str:
                        processes["comment_summarizer"] = {
                            "status": "🟢",
                            "details": f"Running  \n(PID: {proc.info['pid']})",
                        }

                    elif "streamlit" in cmdline_str:
                        processes["streamlit_dashboard"] = {
                            "status": "🟢",
                            "details": f"Running  \n(PID: {proc.info['pid']})",
                        }

                except (
                    psutil.NoSuchProcess,
                    psutil.AccessDenied,
                    psutil.ZombieProcess,
                ):
                    continue

        except Exception as e:

            for process_name in processes.keys():
                processes[process_name] = {
                    "status": "⚠️",
                    "details": f"Cannot check: {str(e)[:30]}",
                }

        return processes

    def check_connection_status(self):

        connection_status = {
            "redis": {"status": "🔴", "details": "Not connected"},
            "mongodb": {"status": "🔴", "details": "Not connected"},
            "youtube_api": {"status": "🔴", "details": "Not tested"},
        }

        try:
            self.redis_client.ping()
            connection_status["redis"] = {"status": "🟢", "details": "Connected"}
        except Exception as e:
            connection_status["redis"] = {
                "status": "🔴",
                "details": f"Error: {str(e)[:50]}",
            }

        try:
            if self.mongo_client:
                self.mongo_client.admin.command("ping")
                connection_status["mongodb"] = {"status": "🟢", "details": "Connected"}
            else:
                connection_status["mongodb"] = {
                    "status": "🔴",
                    "details": "Client not initialized",
                }
        except Exception as e:
            connection_status["mongodb"] = {
                "status": "🔴",
                "details": f"Error: {str(e)[:50]}",
            }

        try:
            url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet&id={config.VIDEO_ID}&key={config.YOUTUBE_API_KEY}"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                connection_status["youtube_api"] = {
                    "status": "🟢",
                    "details": "API responding",
                }
            else:
                connection_status["youtube_api"] = {
                    "status": "🔴",
                    "details": f"HTTP {response.status_code}",
                }
        except Exception as e:
            connection_status["youtube_api"] = {
                "status": "🔴",
                "details": f"Error: {str(e)[:50]}",
            }

        process_status = self.check_process_status()

        combined_status = {
            "connections": connection_status,
            "processes": process_status,
        }

        return combined_status

    def export_data_to_csv(self):
        try:
            comments = self.get_recent_comments(limit=1000)
            if not comments:
                return None

            df = pd.DataFrame(comments)

            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            csv_data = csv_buffer.getvalue()

            return csv_data
        except Exception as e:
            st.error(f"Error exporting to CSV: {e}")
            return None

    def export_data_to_json(self):
        try:
            comments = self.get_recent_comments(limit=1000)
            if not comments:
                return None

            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "video_id": config.VIDEO_ID,
                "total_comments": len(comments),
                "sentiment_counts": self.get_sentiment_counts(),
                "comments": comments,
            }

            return json.dumps(export_data, indent=2, ensure_ascii=False)
        except Exception as e:
            st.error(f"Error exporting to JSON: {e}")
            return None

    def get_video_info(self):
        if self.video_info is not None:
            return self.video_info

        with st.spinner("🔄 Mengambil informasi video..."):
            try:
                url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet&id={config.VIDEO_ID}&key={config.YOUTUBE_API_KEY}"
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                data = response.json()

                if data.get("items"):
                    snippet = data["items"][0]["snippet"]
                    self.video_info = {
                        "title": snippet.get("title", "Judul tidak tersedia"),
                        "channel": snippet.get(
                            "channelTitle", "Channel tidak tersedia"
                        ),
                        "published_at": snippet.get("publishedAt"),
                        "description": (
                            snippet.get("description", "")[:200] + "..."
                            if len(snippet.get("description", "")) > 200
                            else snippet.get("description", "")
                        ),
                    }
                else:
                    st.warning("⚠️ Video tidak ditemukan di YouTube API")
                    self.video_info = {
                        "title": "Video tidak ditemukan",
                        "channel": "Channel tidak tersedia",
                        "published_at": None,
                        "description": "",
                    }
            except requests.exceptions.Timeout:
                self.video_info = {
                    "title": "Error: Timeout",
                    "channel": "Channel tidak tersedia",
                    "published_at": None,
                    "description": "",
                }
            except requests.exceptions.RequestException as e:
                self.video_info = {
                    "title": "Error mengambil judul",
                    "channel": "Channel tidak tersedia",
                    "published_at": None,
                    "description": "",
                }
            except Exception as e:
                self.video_info = {
                    "title": "Error mengambil judul",
                    "channel": "Channel tidak tersedia",
                    "published_at": None,
                    "description": "",
                }

        return self.video_info

    def get_sentiment_counts(self):
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

    def get_recent_comments(self, limit=100):
        try:
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
        if self.mongo_db is None:
            st.error("MongoDB connection not available")
            return None

        try:
            collection_name = f"{config.VIDEO_ID}_summaries"
            collection = self.mongo_db[collection_name]

            latest_summary = collection.find_one({}, sort=[("timestamp", -1)])

            if latest_summary:
                if "_id" in latest_summary:
                    latest_summary["_id"] = str(latest_summary["_id"])

                if "created_at" in latest_summary and hasattr(
                    latest_summary["created_at"], "isoformat"
                ):
                    latest_summary["created_at"] = latest_summary[
                        "created_at"
                    ].isoformat()
                if "processed_at" in latest_summary and hasattr(
                    latest_summary["processed_at"], "isoformat"
                ):
                    latest_summary["processed_at"] = latest_summary[
                        "processed_at"
                    ].isoformat()

                return latest_summary

            return None
        except Exception as e:
            st.error(f"Error getting latest summary from MongoDB: {e}")
            return None

    def get_summary_history(self, limit=10):
        return self.get_summary_history_from_mongodb(limit)

    def init_mongodb(self):
        try:
            self.mongo_client = pymongo.MongoClient(config.MONGODB_CONNECTION_STRING)
            self.mongo_client.admin.command("ping")
            self.mongo_db = self.mongo_client[config.MONGODB_DATABASE]
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            st.error(f"🔴 MongoDB connection failed: {e}")
            self.mongo_client = None
            self.mongo_db = None

    def get_summary_history_from_mongodb(self, limit=None):
        if self.mongo_db is None:
            st.error("MongoDB connection not available")
            return []

        try:
            collection_name = f"{config.VIDEO_ID}_summaries"
            collection = self.mongo_db[collection_name]

            query = {}
            sort_order = [("timestamp", 1)]

            if limit:
                summaries_cursor = collection.find(query).sort(sort_order).limit(limit)
            else:
                summaries_cursor = collection.find(query).sort(sort_order)

            summaries = []
            for doc in summaries_cursor:
                if "_id" in doc:
                    doc["_id"] = str(doc["_id"])
                if "created_at" in doc and hasattr(doc["created_at"], "isoformat"):
                    doc["created_at"] = doc["created_at"].isoformat()
                if "processed_at" in doc and hasattr(doc["processed_at"], "isoformat"):
                    doc["processed_at"] = doc["processed_at"].isoformat()

                summaries.append(doc)

            return summaries

        except Exception as e:
            st.error(f"Error fetching summary history from MongoDB: {e}")
            return []

    def render_metrics(self):
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
        sentiment_counts = self.get_sentiment_counts()

        if sum(sentiment_counts.values()) == 0:
            st.info("No sentiment data available yet")
            return

        labels = [label.title() for label in sentiment_counts.keys()]

        fig = px.pie(
            values=list(sentiment_counts.values()),
            names=labels,
            title="Sentiment Distribution",
            color=labels,
            color_discrete_map={
                "Positive": "#6BCB77",
                "Negative": "#FF6B6B",
                "Neutral": "#4D96FF",
            },
        )

        fig.update_traces(
            textposition="inside",
            textinfo="percent+label",
            textfont=dict(color="white"),
        )
        st.plotly_chart(fig, use_container_width=True)

    def render_recent_comments(self):
        comments = self.get_recent_comments()

        if not comments:
            st.info("No recent comments available")
            return

        df = pd.DataFrame(comments)

        df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.strftime("%H:%M:%S")
        df["confidence"] = df["confidence"].round(3)
        df["sentiment"] = df["sentiment"].str.title()

        def color_sentiment(val):
            if val == "Positive":
                return "background-color: #6BCB77"
            elif val == "Negative":
                return "background-color: #FF6B6B"
            else:
                return "background-color: #4D96FF"

        styled_df = df[
            ["timestamp", "username", "comment", "sentiment", "confidence"]
        ].style.map(color_sentiment, subset=["sentiment"])

        st.dataframe(styled_df, use_container_width=True)

    def render_sentiment_timeline(self):
        comments = self.get_recent_comments(limit=1000)
        if not comments:
            st.info("No data available for sentiment timeline")
            return
        
        df = pd.DataFrame(comments)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        
        df['time_group'] = df['timestamp'].dt.floor('10s')
        
        sentiment_timeline = df.groupby(['time_group', 'sentiment']).size().unstack(fill_value=0)
        
        if sentiment_timeline.empty:
            st.info("No sentiment data available for timeline")
            return
        
        sentiment_timeline = sentiment_timeline.reset_index()
        
        fig = go.Figure()
        colors = {'positive': '#6BCB77', 'negative': '#FF6B6B', 'neutral': '#4D96FF'}
        fill_colors = {'positive': 'rgba(107,203,119,0.2)', 'negative': 'rgba(255,107,107,0.2)', 'neutral': 'rgba(77,150,255,0.2)'}
        
        for sentiment in ['positive', 'negative', 'neutral']:
            if sentiment in sentiment_timeline.columns:
                fig.add_trace(go.Scatter(
                    x=sentiment_timeline['time_group'],
                    y=sentiment_timeline[sentiment],
                    mode='lines+markers',
                    name=sentiment.title(),
                    line=dict(color=colors[sentiment], width=3, shape='spline'),
                    marker=dict(size=8, symbol='circle'),
                    fill='tonexty' if sentiment == 'negative' else None,
                    fillcolor=fill_colors[sentiment]
                ))
        
        fig.update_layout(
            title={
                'text': "📈 Sentiment Timeline Over Time (10-second intervals)",
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 20}
            },
            xaxis_title="Time",
            yaxis_title="Number of Comments",
            hovermode='x unified',
            showlegend=True,
            height=450,
            margin=dict(l=50, r=50, t=80, b=50),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(
                showgrid=True,
                gridwidth=1,
                gridcolor='rgba(128,128,128,0.2)',
                tickformat='%H:%M:%S'
            ),
            yaxis=dict(
                showgrid=True,
                gridwidth=1,
                gridcolor='rgba(128,128,128,0.2)'
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)

    def render_top_active_users(self):
        comments = self.get_recent_comments(limit=500)
        
        if not comments:
            st.info("No data available for top active users")
            return
        
        df = pd.DataFrame(comments)
        user_counts = df['username'].value_counts().head(10)
        
        if user_counts.empty:
            st.info("No user data available")
            return
        
        fig = px.bar(
            x=user_counts.values,
            y=user_counts.index,
            orientation='h',
            labels={'x': 'Number of Comments', 'y': 'Username'},
            color=user_counts.values,
            color_continuous_scale='viridis'
        )
        
        fig.update_layout(
            yaxis={'categoryorder': 'total ascending'},
            height=400,
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)

    def render_trending_words_cloud(self):
        comments = self.get_recent_comments(limit=500)
        
        if not comments:
            st.info("No data available for word cloud")
            return
        
        # Combine all comments
        all_text = ' '.join([comment['comment'] for comment in comments if comment.get('comment')])
        
        if not all_text.strip():
            st.info("No text data available for word cloud")
            return
        
        # Clean text for word cloud
        cleaned_text = re.sub(r'[^\w\s]', ' ', all_text.lower())
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
        
        # Remove common stop words (you can expand this list)
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 
                        'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 
                        'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 
                        'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
                        'a', 'an', 'my', 'your', 'his', 'her', 'its', 'our', 'their', 'me', 'him', 'her', 'us', 'them'}
        
        try:
            # Create word cloud
            wordcloud = WordCloud(
                width=800, 
                height=400, 
                background_color='white',
                max_words=100,
                colormap='viridis',
                stopwords=stop_words
            ).generate(cleaned_text)
            
            # Create matplotlib figure
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.imshow(wordcloud, interpolation='bilinear')
            ax.axis('off')
            ax.set_title('Trending Words Cloud', fontsize=16, pad=20)
            
            st.pyplot(fig)
            plt.close()
            
        except Exception as e:
            st.error(f"Error generating word cloud: {e}")
            # Fallback: show most common words as bar chart
            words = cleaned_text.split()
            word_freq = Counter([word for word in words if len(word) > 3 and word not in stop_words])
            top_words = dict(word_freq.most_common(15))
            
            if top_words:
                fig = px.bar(
                    x=list(top_words.values()),
                    y=list(top_words.keys()),
                    orientation='h',
                    title="🔥 Most Frequent Words",
                    labels={'x': 'Frequency', 'y': 'Words'}
                )
                fig.update_layout(yaxis={'categoryorder': 'total ascending'}, height=400)
                st.plotly_chart(fig, use_container_width=True)

    def render_advanced_visualizations(self):
        self.render_sentiment_timeline()
        
        # Create 2 columns for remaining visualizations
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🏆 Top Active Users")
            self.render_top_active_users()
            
        with col2:
            st.subheader("🔥 Trending Words")
            self.render_trending_words_cloud()

    def render_video_info(self):
        """Render video information section"""
        video_info = self.get_video_info()
        
        with st.container():
            st.subheader("📺 Video Information")
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write(f"**Title:** {video_info['title']}")
                st.write(f"**Channel:** {video_info['channel']}")
                if video_info.get('published_at'):
                    published_date = safe_parse_timestamp(video_info['published_at']).strftime("%Y-%m-%d %H:%M")
                    st.write(f"**Published:** {published_date}")
            
            with col2:
                st.write(f"**Video ID:** `{config.VIDEO_ID}`")
                
    def render_sidebar_system_monitoring(self):
        """Render system monitoring in sidebar"""
        st.sidebar.header("🖥️ System Monitoring")
        status = self.check_connection_status()

        with st.sidebar.expander("🗨️ Process Status", expanded=False):
            for process_name, process_info in status["processes"].items():
                st.write(f"{process_info['status']} **{process_name.replace('_', ' ').title()}**")
                st.caption(process_info['details'])

        with st.sidebar.expander("🔗 Connection Status", expanded=False):
            for conn_name, conn_info in status["connections"].items():
                st.write(f"{conn_info['status']} **{conn_name.upper()}**")
                st.caption(conn_info['details'])

        with st.sidebar.expander("📤 Export Options", expanded=False):
            if st.button("📄 Export CSV", key="export_csv"):
                csv_data = self.export_data_to_csv()
                if csv_data:
                    st.download_button(
                        label="⬇️ Download CSV",
                        data=csv_data,
                        file_name=f"comments_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        key="download_csv"
                    )
            
            if st.button("📋 Export JSON", key="export_json"):
                json_data = self.export_data_to_json()
                if json_data:
                    st.download_button(
                        label="⬇️ Download JSON",
                        data=json_data,
                        file_name=f"comments_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json",
                        key="download_json"
                    )
        
        with st.sidebar.expander("⚡ Quick Actions", expanded=False):
            if st.button("🔄 Refresh Data", key="refresh_data"):
                st.cache_data.clear()
                st.rerun()
            
            if st.button("🧹 Clear Cache", key="clear_cache"):
                try:
                    # Clear Redis cache
                    self.redis_client.flushdb()
                    st.success("✅ Cache cleared successfully!")
                except Exception as e:
                    st.error(f"❌ Error clearing cache: {e}")

    def render_latest_summary(self):
        """Render latest summary section"""
        summary = self.get_latest_summary()

        if not summary:
            st.info("No summary available yet")
            return

        st.subheader("📋 Latest Summary")

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Time Window", f"{config.SUMMARY_WINDOW_MINUTES} minutes")
            st.metric("Total Comments", summary["total_comments"])
        with col2:
            window_start = safe_parse_timestamp(summary["window_start"]).strftime("%H:%M")
            window_end = safe_parse_timestamp(summary["window_end"]).strftime("%H:%M")
            st.metric("Window", f"{window_start} - {window_end}")

        unique_key = f"latest_summary_{uuid.uuid4()}"
        st.text_area(
            "Summary",
            summary["summary"],
            height=400,
            disabled=True,
            key=unique_key,
        )
        
        st.markdown("""
        <style>
        textarea[disabled]{
            color: white !important;
            opacity: 1 !important;
            -webkit-text-fill-color: white !important;
            cursor: text !important;
        }
        </style>
        """, unsafe_allow_html=True)

        if "sentiment_distribution" in summary:
            st.subheader("Sentiment in This Window")
            sentiment_data = []
            
            # Calculate total count for percentage calculation
            total_count = 0
            sentiment_dist = summary["sentiment_distribution"]
            
            # First pass: calculate total count
            for sentiment, stats in sentiment_dist.items():
                if isinstance(stats, dict) and "count" in stats:
                    total_count += stats["count"]
                elif isinstance(stats, (int, float)):
                    total_count += stats
            
            # Second pass: build sentiment data with calculated percentages
            for sentiment, stats in sentiment_dist.items():
                try:
                    if isinstance(stats, dict):
                        count = stats.get("count", 0)
                        # Use existing percentage if available, otherwise calculate it
                        if "percentage" in stats:
                            percentage = stats["percentage"]
                        else:
                            percentage = (count / total_count * 100) if total_count > 0 else 0
                    else:
                        # Handle case where stats is just a number
                        count = stats if isinstance(stats, (int, float)) else 0
                        percentage = (count / total_count * 100) if total_count > 0 else 0
                    
                    sentiment_data.append({
                        "Sentiment": sentiment.title(),
                        "Count": count,
                        "Percentage": f"{percentage:.1f}%"
                    })
                except Exception as e:
                    st.warning(f"Error processing sentiment data for {sentiment}: {e}")
                    # Add fallback data
                    sentiment_data.append({
                        "Sentiment": sentiment.title(),
                        "Count": 0,
                        "Percentage": "0.0%"
                    })
            
            if sentiment_data:
                df_sentiment = pd.DataFrame(sentiment_data)
                st.dataframe(df_sentiment, use_container_width=True)
            else:
                st.info("No sentiment data available for this window")

    def render_summary_history(self):
        """Render summary history section"""
        summaries = self.get_summary_history_from_mongodb()

        if not summaries:
            st.info("No summary history available")
            return

        st.subheader("📚 Summary History")
        st.caption(f"Showing all summaries from oldest to newest ({len(summaries)} total)")

        summaries.reverse()

        for i, summary in enumerate(summaries):
            with st.expander(
                f"📋 Summary #{len(summaries) - i} - {safe_parse_timestamp(summary['window_start']).strftime('%H:%M')} to {safe_parse_timestamp(summary['window_end']).strftime('%H:%M')}",
                expanded=(i == 0)
            ):
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Comments", summary["total_comments"])
                with col2:
                    st.metric("Window", f"{config.SUMMARY_WINDOW_MINUTES} min")
                
                st.text_area(
                    "Summary Content",
                    summary["summary"],
                    height=200,
                    disabled=True,
                    key=f"summary_history_{i}_{uuid.uuid4()}"
                )


def main():
    svg_icon = """
    <svg xmlns="http://www.w3.org/2000/svg" width="50" height="50" fill="red" style="vertical-align:middle;" class="bi bi-youtube" viewBox="0 0 16 16">
    <path d="M8.051 1.999h.089c.822.003 4.987.033 6.11.335a2.01 2.01 0 0 1 1.415 1.42c.101.38.172.883.22 1.402l.01.104.022.26.008.104c.065.914.073 1.77.074 1.957v.075c-.001.194-.01 1.108-.082 2.06l-.008.105-.009.104c-.05.572-.124 1.14-.235 1.558a2.01 2.01 0 0 1-1.415 1.42c-1.16.312-5.569.334-6.18.335h-.142c-.309 0-1.587-.006-2.927-.052l-.17-.006-.087-.004-.171-.007-.171-.007c-1.11-.049-2.167-.128-2.654-.26a2.01 2.01 0 0 1-1.415-1.419c-.111-.417-.185-.986-.235-1.558L.09 9.82l-.008-.104A31 31 0 0 1 0 7.68v-.123c.002-.215.01-.958.064-1.778l.007-.103.003-.052.008-.104.022-.26.01-.104c.048-.519.119-1.023.22-1.402a2.01 2.01 0 0 1 1.415-1.42c.487-.13 1.544-.21 2.654-.26l.17-.007.172-.006.086-.003.171-.007A100 100 0 0 1 7.858 2zM6.4 5.209v4.818l4.157-2.408z"/>    </svg>
    """

    st.markdown(
        f"""
    <h1>{svg_icon} YouTube Live Stream Analytics</h1>
    """,
        unsafe_allow_html=True,
    )
    dashboard = Dashboard()

    dashboard.render_video_info()
    st.divider()
    
    css = """
    <style>
        div[data-baseweb="slider"] {
            margin-left:5px !important;
        }
        div[data-testid="stSidebarUserContent"] {
            padding-top: 40px !important;
        }
        section[data-testid="stSidebar"] h1 {
            margin-top: 0px !important;
        }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
    st.sidebar.header("⚙️ System Setting")

    with st.sidebar.expander("⚙️ Settings", expanded=True):
        auto_refresh = st.checkbox("Auto Refresh", value=True)
        refresh_interval = st.slider("Refresh Interval (seconds)", 3, 10, 3)

    sidebar_status = st.sidebar.empty()
    st.sidebar.markdown(
        """<hr style="margin-top:15px; margin-bottom: 0; !important">""",
        unsafe_allow_html=True
    )
    dashboard.render_sidebar_system_monitoring()
    st.sidebar.markdown(
        """<hr style="margin-top:15px; margin-bottom: 0; !important">""",
        unsafe_allow_html=True
    )
    
    if auto_refresh:
        realtime_placeholder = st.empty()
        st.header("📋 Comment Summaries")
        tab1, tab2 = st.tabs(["Latest Summary", "Summary History"])
        with tab1:
            summary_placeholder = st.empty()
            with summary_placeholder.container():
                dashboard.render_latest_summary()
        with tab2:
            history_placeholder = st.empty()
            with history_placeholder.container():
                dashboard.render_summary_history()

        summary_refresh_interval = (config.SUMMARY_WINDOW_MINUTES * 60) + 5

        last_summary_refresh = time.time()

        while True:
            current_time = time.time()
            
            with realtime_placeholder.container():
                st.header("📊 Real-time Metrics")
                dashboard.render_metrics()
                col1, col2 = st.columns([1, 2])
                with col1:
                    dashboard.render_sentiment_chart()
                with col2:
                    st.subheader("💬 Recent Comments")
                    dashboard.render_recent_comments()
                
                # Advanced Analytics Section
                dashboard.render_advanced_visualizations()
                
                current_timestamp = datetime.now().strftime("%H:%M:%S")
                time_until_refresh = int(
                    summary_refresh_interval - (current_time - last_summary_refresh)
                )

                sidebar_status.markdown(
                    f"""
                    <div style="
                        padding: 15px;
                        margin-bottom: 10px;
                        border-style: solid;
                        border-width: 1px;
                        border-color: rgba(250, 250, 250, 0.2);
                        border-radius: 0.5rem;
                    ">
                        <div style="color: white; font-weight: bold; margin-bottom: 8px;">
                            🔄 <span style="font-size: 14px;">Refresh Status</span>
                        </div>
                        <div style="color: #f0f0f0; font-size: 13px; line-height: 1.5;">
                            <div style="margin-bottom: 5px;">
                                ⏰ <strong>Last Updated:</strong> {current_timestamp}
                            </div>
                            <div style="margin-bottom: 5px;">
                                📋 <strong>Summary Refresh:</strong> {time_until_refresh}
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            
            if current_time - last_summary_refresh >= summary_refresh_interval:
                with summary_placeholder.container():
                    dashboard.render_latest_summary()
                with history_placeholder.container():
                    dashboard.render_summary_history()
                last_summary_refresh = current_time

            time.sleep(refresh_interval)
    else:
        st.header("📊 Real-time Metrics")
        dashboard.render_metrics()
        col1, col2 = st.columns([1, 2])

        with col1:
            dashboard.render_sentiment_chart()

        with col2:
            st.subheader("💬 Recent Comments")
            dashboard.render_recent_comments()
        
        # Advanced Analytics Section
        dashboard.render_advanced_visualizations()
        
        st.header("📋 Comment Summaries")
        tab1, tab2 = st.tabs(["Latest Summary", "Summary History"])
        with tab1:
            dashboard.render_latest_summary()
        with tab2:
            dashboard.render_summary_history()


if __name__ == "__main__":
    main()
