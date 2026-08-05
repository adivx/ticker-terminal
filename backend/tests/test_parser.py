import pytest

from app.parser import CommandError, parse


def test_us_equity_default():
    p = parse("AAPL US Equity <GO>")
    assert p.symbol == "AAPL"
    assert p.country == "US"
    assert p.asset == "Equity"
    assert p.function == "DES"
    assert p.yahoo == "AAPL"
    assert p.special is False


def test_us_equity_with_function():
    p = parse("MSFT US Equity GP <GO>")
    assert p.function == "GP"
    assert p.yahoo == "MSFT"


def test_indian_equity():
    p = parse("RELIANCE IN Equity <GO>")
    assert p.yahoo == "RELIANCE.NS"
    assert p.country == "IN"


def test_bse_equity():
    p = parse("TCS BSE Equity FA <GO>")
    assert p.yahoo == "TCS.BO"
    assert p.function == "FA"


def test_nifty_index():
    p = parse("NIFTY Index GP <GO>")
    assert p.yahoo == "^NSEI"
    assert p.function == "GP"
    assert p.country is None


def test_sensex_index():
    p = parse("SENSEX Index <GO>")
    assert p.yahoo == "^BSESN"
    assert p.function == "DES"


def test_spx_index():
    p = parse("SPX Index <GO>")
    assert p.yahoo == "^GSPC"


def test_bare_symbol_defaults_us():
    p = parse("AAPL")
    assert p.yahoo == "AAPL"
    assert p.function == "DES"
    assert p.country == "US"


def test_specials():
    for raw, fn in [("TOP <GO>", "TOP"), ("WEI", "WEI"), ("HELP <GO>", "HELP")]:
        p = parse(raw)
        assert p.special is True
        assert p.function == fn


def test_case_insensitive():
    p = parse("aapl us equity gp <go>")
    assert p.yahoo == "AAPL"
    assert p.function == "GP"


def test_currency():
    p = parse("USDJPY Curncy <GO>")
    assert p.yahoo == "USDJPY=X"
    assert p.function == "DES"


def test_unknown_function_rejected():
    with pytest.raises(CommandError):
        parse("AAPL US Equity FOO <GO>")


def test_empty_rejected():
    with pytest.raises(CommandError):
        parse("   ")
    with pytest.raises(CommandError):
        parse("")


def test_go_stripped_anywhere():
    p = parse("NVDA US Equity <go>")
    assert p.symbol == "NVDA"
    assert p.yahoo == "NVDA"
