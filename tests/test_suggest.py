from histalias.suggest import RESERVED, suggest_name


def test_initials_of_significant_words():
    name = suggest_name("git push origin main", taken=set())
    assert name == "gpom"


def test_stopwords_are_skipped():
    name = suggest_name("tail -f /var/log/syslog", taken=set())
    # "-f" flag ignored, "tail var log syslog" -> "tvls"
    assert name == "tvls"


def test_collision_falls_back_to_shorter_name():
    name = suggest_name("git push origin main", taken={"gpom"})
    assert name == "gpo"


def test_reserved_names_never_generated():
    for cmd in ["list stuff", "change directory", "copy my files"]:
        name = suggest_name(cmd, taken=set())
        assert name not in RESERVED


def test_gibberish_returns_none():
    assert suggest_name("!!! ???", taken=set()) is None


def test_single_word_command():
    # "kubectl" -> 3-letter head fallback
    assert suggest_name("kubectl", taken=set()) == "kub"
