import streamlit as st


def compute_about(*args, **kwargs):
    st.title("About")
    st.markdown("Site by <a href='mailto:admin@thetower.lol'>`098799`</a>.", unsafe_allow_html=True)
    st.markdown("Thanks to `andreasjn` for the help with the discord bot.")
    st.markdown("Thanks to `Milamber33` for a lot of help with css and other things.")
    st.markdown("Thanks to `Jim808`, `ObsUK` and `Bartek` for a graph ideas and encouragement.")
    st.markdown("Thanks to `Fnord`, `Neothin87`, `imsaguy` and others for the encouragement, ideas, security audits.")
    st.markdown("Thanks to `Pog` and the discord mods for all the work on sus reports.")

    st.header("Sus people")
    st.write(
        """Sometimes on the leaderboards there are suspicious individuals that had achieved hard to believe tournament scores. The system doesn't necessarily manage to detect and flag all of them, so some postprocessing is required. There's no official approval board for this, I'm just a guy on discord that tries to analyze results. If you'd like your name rehabilitated, please join the tower discord and talk to us in the tournament channel."""
    )
    st.write(
        """It is important to note that **not all people listed here are confirmed hackers**!! In fact, Pog has explicitly stated that some of them may not be hackers, or at least it cannot be proven at this point."""
    )

    # st.write("Currently, sus people are:")

    # st.write(pd.DataFrame(get_sus_data()).to_html(escape=False), unsafe_allow_html=True)

    # # st.header("Vindicated")
    # # st.write("Previously on the sus list but vindicated by the tower staff:")
    # # st.write(sorted([nickname for nickname, id_ in rehabilitated]))
