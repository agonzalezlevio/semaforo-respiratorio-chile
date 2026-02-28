"""Tests for pipeline.ingest module."""

from pipeline.ingest import map_cause, normalize_cause


class TestNormalizeCause:
    def test_strips_whitespace(self):
        assert normalize_cause("  INFLUENZA  ") == "INFLUENZA"

    def test_collapses_double_spaces(self):
        assert normalize_cause("TOTAL  CAUSA  SISTEMA  RESPIRATORIO") == "TOTAL CAUSA SISTEMA RESPIRATORIO"

    def test_handles_tabs_and_newlines(self):
        assert normalize_cause("IRA\t ALTA\n") == "IRA ALTA"

    def test_handles_non_string(self):
        result = normalize_cause(123)
        assert result == "123"


class TestMapCause:
    def test_total(self):
        assert map_cause("TOTAL CAUSA SISTEMA RESPIRATORIO") == "Total"

    def test_ira_alta(self):
        assert map_cause("IRA ALTA") == "IRA Alta"

    def test_influenza(self):
        assert map_cause("INFLUENZA") == "Influenza"

    def test_covid_total_identified(self):
        assert map_cause("TOTAL ATENCIONES POR COVID-19, Virus Identificado U07.1") == "COVID-19"

    def test_covid_total_not_identified(self):
        assert map_cause("TOTAL ATENCIONES POR COVID-19  Virus no Identificado U07.2") == "COVID-19"

    def test_covid_sub_identified(self):
        assert map_cause("- Por covid-19, virus identificado U07.1") == "COVID-19"

    def test_covid_sub_not_identified(self):
        assert map_cause("- Por covid-19, virus no identificado U07.2") == "COVID-19"

    def test_neumonia(self):
        assert map_cause("NEUMONIA") == "Neumonía"

    def test_neumonia_with_encoding_issue(self):
        # Simulates encoding corruption where ñ becomes something else
        # The prefix "NEUMON" still matches
        assert map_cause("NEUMON\xcdA") == "Neumonía"

    def test_bronquitis_maps_to_bronquitis(self):
        assert map_cause("BRONQUITIS/BRONQUIOLITIS AGUDA") == "Bronquitis"

    def test_crisis_obstructiva_maps_to_obstructiva(self):
        assert map_cause("CRISIS OBSTRUCTIVA BRONQUIAL") == "Obstructiva"

    def test_subtotal_maps_to_subtotal(self):
        assert map_cause("- Causas sistema respiratorio (J00-J98)") == "_subtotal"

    def test_unknown_maps_to_otra_resp(self):
        assert map_cause("SOMETHING ELSE ENTIRELY") == "Otra resp."

    def test_case_insensitive(self):
        assert map_cause("influenza") == "Influenza"
        assert map_cause("ira alta") == "IRA Alta"
