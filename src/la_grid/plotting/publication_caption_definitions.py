"""Concise shared scientific definitions; no numerical-result changes."""


def refine(records):
    definitions = {
        'workflow': 'PGA denotes peak ground acceleration; DS, damage state; GA, genetic algorithm.',
        'network_dependencies': 'CEC is the California Energy Commission; SCE, Southern California Edison; LADWP, the Los Angeles Department of Water and Power.',
        'damage_service': 'DS denotes damage state.',
        'source_connectivity': 'Core sources are the prescribed source substations in the retained graph.',
        'strategy_performance': 'Q4 is the highest frozen social-vulnerability quartile; hospital-linked denotes tract association, not hospital electricity demand.',
        'distributional_effects': 'Q1/Q4 are the lowest/highest frozen social-vulnerability quartiles. Gini summarizes tract service-loss inequality.',
        'resource_effects': 'Q1/Q4 are the lowest/highest frozen social-vulnerability quartiles.',
        'community_context': 'HHI is the Herfindahl-Hirschman index of tract dependency-weight concentration; RQ denotes research question. SOVI is the social-vulnerability score. The five-policy mean includes Impact-, Hospital-, Degree-, Betweenness-, and Vulnerability-first, excluding Random.',
        'restoration_logistics': 'LADWP is the Los Angeles Department of Water and Power; SCE, Southern California Edison.',
        'ga_evaluation': 'GA denotes genetic algorithm.',
        'facility_limits': 'SCE denotes Southern California Edison.',
        'priority_geography': 'Q4 is the highest frozen social-vulnerability quartile.',
        'resource_outcomes': 'Q1/Q4 are the lowest/highest frozen social-vulnerability quartiles.'
    }
    replacements = {
        'community_context': [('frozen FEMA NRI v1.19', 'Federal Emergency Management Agency (FEMA) National Risk Index (NRI) v1.19')],
        'mapping_gate_sensitivity': [('M1 mapping cutoff', 'tract-substation mapping cutoff')],
        'damage_geography': [('not physical MW or observed customer outages', 'not delivered electric power or observed customer outages')],
        'priority_geography': [('C shades log population', 'C shows population on a logarithmic color scale')]
    }
    result = {}
    changes = []
    for identity, (title, body) in records.items():
        original = body
        for old, new in replacements.get(identity, []):
            assert old in body, (identity, old)
            body = body.replace(old, new, 1)
        if identity in definitions:
            body += ' ' + definitions[identity]
        result[identity] = [title, body]
        if body != original:
            changes.append(dict(identity=identity, before=original, after=body,
                                scope='Definitions/abbreviations only; no result numbers or uncertainty rules changed.'))
    return result, changes
