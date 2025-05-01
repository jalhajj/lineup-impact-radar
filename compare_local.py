import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from math import pi
import ast

st.set_page_config(layout="wide")
st.title("🏀 Lineup Impact Radar: With vs Without / Partial Overlap")

# File uploader
uploaded_file = st.file_uploader("📁 Upload your lineup stats CSV", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df['lineup'] = df['lineup'].astype(str)

    if 'team' not in df.columns:
        st.error("❌ 'team' column not found in uploaded CSV. Please include it in your dataset.")
    else:
        team_options = sorted(df['team'].dropna().unique().tolist())
        selected_team = st.selectbox("🔍 Select Team", team_options)

        # Filter by team
        team_df = df[df['team'] == selected_team]

        # Filter by opponent
        opponent_options = ['All'] + sorted(team_df['opponent_team'].dropna().unique().tolist())
        selected_opponent = st.selectbox("🎯 Filter by Opponent", opponent_options)

        if selected_opponent != 'All':
            team_df = team_df[team_df['opponent_team'] == selected_opponent]

        # Parse lineup safely
        team_df['parsed_lineup'] = team_df['lineup'].apply(lambda x: list(ast.literal_eval(x)))

        # Build player pool
        all_players = sorted(set(p for lineup in team_df['parsed_lineup'] for p in lineup))
        selected_players = st.multiselect("👥 Select up to 5 players", all_players, max_selections=5)

        # Comparison type
        comparison_type = st.radio("📊 Choose comparison type", ["With vs Without", "With vs Partial Overlap"])

        def get_radar_stats(df):
            fg = df['FG Made'].sum() / df['FG Attempted'].sum() * 100 if df['FG Attempted'].sum() > 0 else 0
            efg = ((df['FG Made'].sum() + 0.5 * df['3pt_made'].sum()) / df['FG Attempted'].sum() * 100) if df['FG Attempted'].sum() > 0 else 0
            tov = df['TOV%'].mean()
            reb = df['rebounds'].sum() / (df['rebounds'].sum() + df['opponent_rebounds'].sum()) * 100 if (df['rebounds'].sum() + df['opponent_rebounds'].sum()) > 0 else 0
            steals = df['Steals%'].mean()
            three_share = (df['3pt_made'].sum() + df['3pt_missed'].sum()) / df['FG Attempted'].sum() * 100 if df['FG Attempted'].sum() > 0 else 0
            two_share = (df['2pt_made'].sum() + df['2pt_missed'].sum()) / df['FG Attempted'].sum() * 100 if df['FG Attempted'].sum() > 0 else 0
            opp_fg = df['Opponent FG Made'].sum() / df['Opponent FG Attempted'].sum() * 100 if df['Opponent FG Attempted'].sum() > 0 else 0
            opp_efg = ((df['Opponent FG Made'].sum() + 0.5 * df['opponent_3pt_made'].sum()) / df['Opponent FG Attempted'].sum() * 100) if df['Opponent FG Attempted'].sum() > 0 else 0
            opp_tov = df['Opponent TOV%'].mean()
            opp_reb = df['opponent_rebounds'].sum() / (df['rebounds'].sum() + df['opponent_rebounds'].sum()) * 100 if (df['rebounds'].sum() + df['opponent_rebounds'].sum()) > 0 else 0
            opp_steals = df['Opponent Steals%'].mean()
            return [fg, efg, tov, reb, steals, three_share, two_share, opp_fg, opp_efg, opp_tov, opp_reb, opp_steals]

        if selected_players:
            with_players = team_df[team_df['parsed_lineup'].apply(lambda x: all(p in x for p in selected_players))]
            without_players = team_df[team_df['parsed_lineup'].apply(lambda x: all(p not in x for p in selected_players))]
            partial_overlap = team_df[
                team_df['parsed_lineup'].apply(lambda x: any(p in x for p in selected_players) and not all(p in x for p in selected_players))
            ]

            if comparison_type == "With vs Without":
                group_a = with_players
                group_b = without_players
                label_b = "Without Selected Players"
            else:
                group_a = with_players
                group_b = partial_overlap
                label_b = "Partial Overlap"

            with_stats = get_radar_stats(group_a)
            group_b_stats = get_radar_stats(group_b)

            categories = ['FG%', 'eFG%', 'TOV%', 'Reb%', 'Steals%', '3PT Share', '2PT Share',
                          'Opp FG%', 'Opp eFG%', 'Opp TOV%', 'Opp Reb%', 'Opp Steals%']
            angles = [n / float(len(categories)) * 2 * pi for n in range(len(categories))]
            angles += angles[:1]

            with_stats += with_stats[:1]
            group_b_stats += group_b_stats[:1]

            # Radar chart
            fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
            ax.plot(angles, with_stats, linewidth=2, label="With Selected Players")
            ax.fill(angles, with_stats, alpha=0.25)
            ax.plot(angles, group_b_stats, linewidth=2, linestyle='dashed', label=label_b)
            ax.fill(angles, group_b_stats, alpha=0.15)

            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(categories, fontsize=10)
            ax.set_title("🎯 Lineup Impact Comparison", y=1.1)
            ax.legend(loc='upper right', bbox_to_anchor=(1.4, 1.1))

            st.pyplot(fig)

            st.subheader("📋 Metrics Summary")
            df_summary = pd.DataFrame({
                'Metric': categories,
                'With Selected': with_stats[:-1],
                label_b: group_b_stats[:-1]
            })
            st.dataframe(df_summary.reset_index(drop=True), use_container_width=True)

            st.subheader("📊 Raw Totals Comparison")
            total_stats = [
                "points", "rebounds", "turnovers", "assists", "steals", "FG Made", "FG Attempted",
                "3pt_made", "3pt_missed", "2pt_made", "2pt_missed", "duration", 
                "ORTG", "DRTG"
            ]
            raw_a = group_a[total_stats].sum()
            raw_b = group_b[total_stats].sum()
            raw_df = pd.DataFrame({
                "Stat": total_stats,
                "With Selected": raw_a.values,
                label_b: raw_b.values
            })
            st.dataframe(raw_df.reset_index(drop=True), use_container_width=True)
            
            pbp_a = group_a[total_stats].mean()
            pbp_b = group_b[total_stats].mean()
            pbp_df = pd.DataFrame({
                "Stat": total_stats,
                "With Selected": pbp_a.values,
                label_b: pbp_b.values
            })
            st.dataframe(pbp_df.reset_index(drop=True), use_container_width=True)
