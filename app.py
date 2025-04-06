# app.py
import streamlit as st
import pandas as pd
import random
from helper import load_performance, save_performance


class FlagQuiz:
    def __init__(self, df):
        self.df = df
        self.performance = st.session_state.get("performance", load_performance())
        st.session_state.performance = self.performance

        self.current_country = st.session_state.get("current_country")
        self.choices = st.session_state.get("choices", [])
        self.user_guess = st.session_state.get("user_guess")
        self.submitted = st.session_state.get("submitted", False)

        if self.current_country is None:
            self.current_country = self.select_next_country()
            st.session_state.current_country = self.current_country

    def select_next_country(self, epsilon=0.1):
        if random.random() < epsilon:
            return self.df.sample(1).iloc[0]  # explore

        def score(code):
            stats = self.performance.get(code, {"correct": 0, "wrong": 0})
            return stats["correct"] - stats["wrong"]

        sorted_df = self.df.copy()
        sorted_df["score"] = sorted_df["Code"].apply(score)
        return sorted_df.sort_values("score").iloc[0]

    def generate_choices(self):
        if not self.choices:
            choices = random.sample(list(self.df["Name"]), 3)
            if self.current_country["Name"] not in choices:
                choices[random.randint(0, 2)] = self.current_country["Name"]
            random.shuffle(choices)
            self.choices = choices
            st.session_state.choices = choices

    def submit_guess(self, guess):
        code = self.current_country["Code"]
        stats = self.performance.setdefault(code, {"correct": 0, "wrong": 0})

        if guess == self.current_country["Name"]:
            st.success("✅ Correct!")
            stats["correct"] += 1
        else:
            st.error(f"❌ Incorrect. It was **{self.current_country['Name']}**.")
            stats["wrong"] += 1

        save_performance(self.performance)
        self.user_guess = guess
        self.submitted = True
        st.session_state.user_guess = guess
        st.session_state.submitted = True

    def next_country(self):
        st.session_state.current_country = self.select_next_country()
        st.session_state.choices = []
        st.session_state.user_guess = None
        st.session_state.submitted = False
        st.rerun()

    def render_flag(self):
        flag_url = f"https://flagcdn.com/w320/{self.current_country['Code'].lower()}.png"
        st.image(flag_url, width=300)

    def render_stats(self):
        st.markdown("## 📊 Your Performance So Far")
        if not self.performance:
            st.info("You haven't answered any flags yet.")
            return

        stats_df = pd.DataFrame.from_dict(self.performance, orient="index")
        stats_df["Total"] = stats_df["correct"] + stats_df["wrong"]
        stats_df["Accuracy (%)"] = (100 * stats_df["correct"] / stats_df["Total"]).round(1)

        code_to_country = dict(zip(self.df["Code"], self.df["Name"]))
        stats_df["Name"] = stats_df.index.map(code_to_country)
        stats_df = stats_df[["Name", "correct", "wrong", "Total", "Accuracy (%)"]]
        stats_df = stats_df.sort_values("Accuracy (%)")

        st.dataframe(stats_df.reset_index(drop=True), use_container_width=True)


# --- App Start ---
st.set_page_config(page_title="Flag Quiz", page_icon="🏳️")
st.title("🏳️ Flag Quiz")

df = pd.read_csv("countries.csv")
quiz = FlagQuiz(df)
quiz.generate_choices()
quiz.render_flag()
st.markdown("### Which country is this flag from?")

# --- Form for Guess ---
with st.form("quiz_form", clear_on_submit=False):
    guess = st.selectbox(
        "Type or select the country name:",
        options=sorted(df["Name"].unique()),
        key="country_input"
    )
    col1, col2 = st.columns([1, 1])
    submit_clicked = col1.form_submit_button("✅ Submit")
    next_clicked = col2.form_submit_button("➡️ Next")

# --- Handle Submission ---
if submit_clicked and not quiz.submitted:
    quiz.submit_guess(guess)

if next_clicked:
    quiz.next_country()

# --- Show Stats ---
quiz.render_stats()
