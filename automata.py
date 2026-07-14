import re

KEYWORDS  = {'int','float','bool','string','char','if','else','while','for','return','void','true','false'}
DIGITS    = list('0123456789')
LETTERS   = list('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_')
ALPHANUMS = LETTERS + DIGITS
SIGMA     = (list('abcdefghijklmnopqrstuvwxyz') +
             list('ABCDEFGHIJKLMNOPQRSTUVWXYZ') +
             list('0123456789') +
             list('_=+-*/<>!%(){}[];\'"') +
             list(','))


# ── STATE ─────────────────────────────────────────────────────────────────────

class State:
    def __init__(self, label):
        self.label       = label
        self.transitions = {}
        self.epsilon     = []

    def add_transition(self, char, target):
        self.transitions.setdefault(char, [])
        if target not in self.transitions[char]:
            self.transitions[char].append(target)

    def __repr__(self):
        return self.label


class NFAMachine:
    def __init__(self, start, accept, states):
        self.start  = start
        self.accept = accept
        self.states = states


# ── THOMPSON BUILDER ──────────────────────────────────────────────────────────

class Thompson:
    def __init__(self):
        self._n = 0

    def _s(self):
        s = State(f"q{self._n}"); self._n += 1; return s

    def char(self, c):
        s0, s1 = self._s(), self._s()
        s0.add_transition(c, s1)
        return NFAMachine(s0, s1, [s0, s1])

    def char_class(self, chars):
        """All chars in class share one target — compact 2-state NFA."""
        s0, s1 = self._s(), self._s()
        for c in chars:
            s0.add_transition(c, s1)
        return NFAMachine(s0, s1, [s0, s1])

    def literal(self, s):
        nfa = self.char(s[0])
        for c in s[1:]:
            nfa = self.concat(nfa, self.char(c))
        return nfa

    def concat(self, n1, n2):
        n1.accept.epsilon.append(n2.start)
        return NFAMachine(n1.start, n2.accept, n1.states + n2.states)

    def union(self, n1, n2):
        s, a = self._s(), self._s()
        s.epsilon = [n1.start, n2.start]
        n1.accept.epsilon.append(a)
        n2.accept.epsilon.append(a)
        return NFAMachine(s, a, [s] + n1.states + n2.states + [a])

    def star(self, n):
        s, a = self._s(), self._s()
        s.epsilon        = [n.start, a]
        n.accept.epsilon = [n.start, a]
        return NFAMachine(s, a, [s] + n.states + [a])

    def plus(self, chars):
        """[chars]+ = char_class . star(fresh char_class)"""
        n1 = self.char_class(chars)
        n2 = self.char_class(chars)
        return self.concat(n1, self.star(n2))


# ── TOKEN NFA BUILDERS ────────────────────────────────────────────────────────

def build_token_nfa(t, tok_type, lexeme):
    if tok_type == 'KEYWORD':
        return t.literal(lexeme)
    elif tok_type == 'INTEGER':
        return t.plus(DIGITS)
    elif tok_type == 'FLOAT':
        return t.concat(t.concat(t.plus(DIGITS), t.char('.')), t.plus(DIGITS))
    elif tok_type == 'IDENTIFIER':
        return t.concat(t.char_class(LETTERS), t.star(t.char_class(ALPHANUMS)))
    elif tok_type == 'OPERATOR':
        return t.literal(lexeme)
    elif tok_type == 'SEPARATOR':
        return t.char(lexeme)
    else:
        return t.literal(lexeme)


# ── EPSILON-CLOSURE & MOVE ────────────────────────────────────────────────────

def epsilon_closure(states):
    seen = set(); stack = []; result = []
    for s in states:
        if id(s) not in seen:
            seen.add(id(s)); stack.append(s); result.append(s)
    while stack:
        cur = stack.pop()
        for t in cur.epsilon:
            if id(t) not in seen:
                seen.add(id(t)); stack.append(t); result.append(t)
    return result


def move(states, symbol):
    result = []; seen = set()
    for s in states:
        for t in s.transitions.get(symbol, []):
            if id(t) not in seen:
                seen.add(id(t)); result.append(t)
    return result


def get_all_symbols(nfa_states):
    syms = set()
    for s in nfa_states:
        syms.update(s.transitions.keys())
    return sorted(syms)


def _sort_key(label):
    m = re.match(r'^q(\d+)$', str(label))
    return int(m.group(1)) if m else 999


# ── EPSILON-NFA TABLE EXPORT ──────────────────────────────────────────────────

def enfa_to_dict(nfa):
    """Export raw Thompson ε-NFA states sorted numerically."""
    sorted_states = sorted(nfa.states, key=lambda s: _sort_key(s.label))
    rows = []
    for s in sorted_states:
        rows.append({
            'state'      : s.label,
            'is_start'   : s is nfa.start,
            'is_accept'  : s is nfa.accept,
            'epsilon'    : [t.label for t in s.epsilon],
            'transitions': {sym: [t.label for t in tgts]
                            for sym, tgts in s.transitions.items()},
        })
    return rows


# ── NFA TABLE (epsilon-closure groups, equivalent states merged) ───────────────

def build_nfa_table(nfa):
    all_states = nfa.states
    syms       = get_all_symbols(all_states)
    lbl_map    = {s.label: s for s in all_states}

    def ec_of_labels(labels):
        states  = [lbl_map[l] for l in labels if l in lbl_map]
        closure = epsilon_closure(states)
        return frozenset(s.label for s in closure)

    def move_labels(fs_labels, sym):
        states  = [lbl_map[l] for l in fs_labels if l in lbl_map]
        reached = move(states, sym)
        return frozenset(s.label for s in reached)

    start_ec = ec_of_labels([nfa.start.label])
    visited  = {}   # frozenset -> group name "S0", "S1", ...
    queue    = [start_ec]
    order    = []
    idx      = [0]

    def name_of(fs):
        if fs not in visited:
            visited[fs] = f"S{idx[0]}"; idx[0] += 1
        return visited[fs]

    name_of(start_ec)

    while queue:
        cur_fs = queue.pop(0)
        if cur_fs in order:
            continue
        order.append(cur_fs)
        for sym in syms:
            moved = move_labels(cur_fs, sym)
            if not moved:
                continue
            next_ec = ec_of_labels(list(moved))
            if next_ec not in visited:
                name_of(next_ec)
                queue.append(next_ec)

    raw_table = []
    for fs in order:
        name      = visited[fs]
        is_start  = (fs == start_ec)
        is_accept = (nfa.accept.label in fs)
        trans     = {}
        for sym in syms:
            moved = move_labels(fs, sym)
            if not moved:
                continue
            next_ec = ec_of_labels(list(moved))
            if next_ec in visited:
                trans[sym] = [visited[next_ec]]
        raw_table.append({
            'state'           : name,
            'epsilon_closure' : sorted(fs, key=_sort_key),
            'is_start_closure': is_start,
            'is_nfa_accept'   : is_accept,
            'transitions'     : trans,
        })

    # Merge equivalent groups
    def sig(row):
        return (row['is_nfa_accept'], tuple(
            (sym, tuple(sorted(row['transitions'].get(sym, []))))
            for sym in syms
        ))

    sig_groups = {}
    for row in raw_table:
        s = sig(row)
        sig_groups.setdefault(s, []).append(row['state'])

    canon = {}
    for group_list in sig_groups.values():
        rep = group_list[0]
        for s in group_list:
            row = next(r for r in raw_table if r['state'] == s)
            if row['is_start_closure']:
                rep = s; break
        for s in group_list:
            canon[s] = rep

    seen_reps = set()
    merged    = []
    for row in raw_table:
        rep = canon[row['state']]
        if rep in seen_reps:
            continue
        seen_reps.add(rep)
        members  = [r for r in raw_table if canon[r['state']] == rep]
        all_ec   = sorted({l for r in members for l in r['epsilon_closure']}, key=_sort_key)
        new_trans = {}
        for sym, tgts in row['transitions'].items():
            new_trans[sym] = list(dict.fromkeys(canon.get(t, t) for t in tgts))
        merged.append({
            'state'           : rep,
            'epsilon_closure' : all_ec,
            'is_start_closure': row['is_start_closure'],
            'is_nfa_accept'   : row['is_nfa_accept'],
            'transitions'     : new_trans,
        })

    nd_count = sum(
        1 for row in merged
        for tgts in row['transitions'].values()
        if len(tgts) > 1
    )

    return {
        'table'        : merged,
        'symbols'      : syms,
        'start_closure': sorted(start_ec, key=_sort_key),
        'accept_states': [r['state'] for r in merged if r['is_nfa_accept']],
        'nd_count'     : nd_count,
        'overlap_note' : None,
    }


# ── DFA — SUBSET CONSTRUCTION ─────────────────────────────────────────────────

def build_dfa(nfa):
    all_states   = nfa.states
    syms         = get_all_symbols(all_states)
    accept_label = nfa.accept.label
    lbl_map      = {s.label: s for s in all_states}
    DEAD         = 'DEAD'

    # Use full explicit alphabet — no 'other' catch-all
    syms = sorted(set(SIGMA) | set(syms))

    def ec_fs(labels):
        states  = [lbl_map[l] for l in labels if l in lbl_map]
        closure = epsilon_closure(states)
        return frozenset(s.label for s in closure)

    def move_fs(labels, sym):
        states  = [lbl_map[l] for l in labels if l in lbl_map]
        reached = move(states, sym)
        return frozenset(s.label for s in reached)

    name_seq = [0]; dfa_names = {}

    def get_name(fs):
        if fs not in dfa_names:
            n = name_seq[0]; name_seq[0] += 1
            dfa_names[fs] = f"q{n}"
        return dfa_names[fs]

    start_fs = ec_fs([nfa.start.label])
    get_name(start_fs)

    queue = [start_fs]; visited = set(); raw_table = []; trap_needed = False

    while queue:
        cur_fs = queue.pop(0)
        if cur_fs in visited:
            continue
        visited.add(cur_fs)

        name      = get_name(cur_fs)
        is_start  = (cur_fs == start_fs)
        is_accept = (accept_label in cur_fs)
        row_trans = {}

        for sym in syms:
            moved_raw = move_fs(cur_fs, sym)
            if not moved_raw:
                row_trans[sym] = DEAD
                trap_needed    = True
            else:
                next_fs        = ec_fs(moved_raw)
                next_name      = get_name(next_fs)
                row_trans[sym] = next_name
                if next_fs not in visited:
                    queue.append(next_fs)

        # Compute dead_symbols and live_symbols for Sigma notation
        dead_syms = [sym for sym, tgt in row_trans.items() if tgt == DEAD]
        live_syms = [sym for sym, tgt in row_trans.items() if tgt != DEAD]

        raw_table.append({
            'state'       : name,
            'is_start'    : is_start,
            'is_accept'   : is_accept,
            'is_trap'     : False,
            'nfa_states'  : sorted(cur_fs, key=_sort_key),
            'transitions' : row_trans,
            'dead_symbols': dead_syms,
            'live_symbols': live_syms,
            '_fs'         : cur_fs,
        })

    if trap_needed:
        raw_table.append({
            'state'       : DEAD,
            'is_start'    : False,
            'is_accept'   : False,
            'is_trap'     : True,
            'nfa_states'  : [],
            'transitions' : {sym: DEAD for sym in syms},
            'dead_symbols': list(syms),  # all 82 chars
            'live_symbols': [],
            '_fs'         : frozenset(),
        })
    # Minimize DFA
    min_table = minimize_dfa(raw_table, syms, DEAD)
    for row in min_table:
        dead_syms = [sym for sym, tgt in row['transitions'].items() if tgt == DEAD]
        live_syms = [sym for sym, tgt in row['transitions'].items() if tgt != DEAD]
        row['dead_symbols'] = dead_syms
        row['live_symbols'] = live_syms

    # Keep full DFA (pre-minimization) for display.
    # raw_table already includes the DEAD trap row, so copying it gives
    # a complete table. Compute dead/live symbols for every row including
    # the DEAD trap row itself, then strip the internal _fs key.
    full_table = [dict(r) for r in raw_table]
    for row in full_table:
        row.pop('_fs', None)
        row['dead_symbols'] = [sym for sym, tgt in row['transitions'].items() if tgt == DEAD]
        row['live_symbols'] = [sym for sym, tgt in row['transitions'].items() if tgt != DEAD]

    # Compute display_symbols: live symbols first (those with at least one non-DEAD transition),
    # so the analyzer table shows meaningful columns instead of all-DEAD columns.
    live_in_min = sorted({sym for row in min_table if not row['is_trap']
                          for sym, tgt in row['transitions'].items() if tgt != DEAD})
    dead_only   = [s for s in syms if s not in live_in_min]
    display_syms = live_in_min + dead_only

    return {
        'table'             : min_table,
        'full_table'        : full_table,
        'accept_states'     : [r['state'] for r in min_table if r['is_accept']],
        'start_state'       : next(r['state'] for r in min_table if r['is_start']),
        'full_accept_states': [r['state'] for r in full_table if r['is_accept']],
        'full_start_state'  : next(r['state'] for r in full_table if r['is_start']),
        'symbols'           : display_syms,
        'alphabet'          : syms,
        'has_trap'          : any(r['is_trap'] for r in min_table),
        'subset_steps'      : [],
    }


# ── DFA MINIMIZATION (Hopcroft) ───────────────────────────────────────────────

def minimize_dfa(table, syms, DEAD):
    if not table:
        return table

    state_names = [r['state'] for r in table]
    state_map   = {r['state']: r for r in table}

    accepts = frozenset(r['state'] for r in table if r['is_accept'])
    traps   = frozenset(r['state'] for r in table if r['is_trap'])
    non_acc = frozenset(r['state'] for r in table if not r['is_accept'] and not r['is_trap'])

    partitions = []
    if accepts:  partitions.append(accepts)
    if non_acc:  partitions.append(non_acc)
    if traps:    partitions.append(traps)

    def find_group(state, parts):
        for i, p in enumerate(parts):
            if state in p:
                return i
        return -1

    changed = True
    while changed:
        changed   = False
        new_parts = []
        for group in partitions:
            if len(group) <= 1:
                new_parts.append(group); continue
            sig_map = {}
            for s in group:
                row = state_map[s]
                sig = tuple(find_group(row['transitions'].get(sym, DEAD), partitions) for sym in syms)
                sig_map.setdefault(sig, set()).add(s)
            splits = list(sig_map.values())
            new_parts.extend(frozenset(sp) for sp in splits)
            if len(splits) > 1:
                changed = True
        partitions = new_parts

    def pick_rep(group):
        for s in group:
            if state_map[s]['is_start']:
                return s
        return sorted(group)[0]

    group_of = {}
    for g in partitions:
        rep = pick_rep(g)
        for s in g:
            group_of[s] = rep

    reps = list(dict.fromkeys(group_of[s] for s in state_names))

    def rep_sort(rep):
        r = state_map[rep]
        if r['is_start']:  return (0, rep)
        if r['is_accept']: return (1, rep)
        if r['is_trap']:   return (3, rep)
        return (2, rep)

    reps.sort(key=rep_sort)

    # Rename reps to q0, q1, q2... (DEAD stays DEAD)
    rename = {}
    qi = 0
    for rep in reps:
        if state_map[rep]['is_trap']:
            rename[rep] = DEAD
        else:
            rename[rep] = f"q{qi}"; qi += 1

    merged = []
    for rep in reps:
        old      = state_map[rep]
        new_name = rename[rep]
        new_trans = {sym: rename.get(group_of.get(tgt, tgt), tgt)
                     for sym, tgt in old['transitions'].items()}
        # Ensure every symbol in syms has an entry; missing ones go to DEAD
        for sym in syms:
            if sym not in new_trans:
                new_trans[sym] = DEAD
        members  = [s for s in state_names if group_of[s] == rep]
        all_nfa  = sorted({ns for s in members for ns in state_map[s].get('nfa_states', [])}, key=_sort_key)
        dead_syms = [sym for sym, tgt in new_trans.items() if tgt == DEAD]
        live_syms = [sym for sym, tgt in new_trans.items() if tgt != DEAD]
        merged.append({
            'state'       : new_name,
            'is_start'    : old['is_start'],
            'is_accept'   : old['is_accept'],
            'is_trap'     : old['is_trap'],
            'nfa_states'  : all_nfa,
            'transitions' : new_trans,
            'dead_symbols': dead_syms,
            'live_symbols': live_syms,
        })

    return merged


# ── DFA SIMULATION ────────────────────────────────────────────────────────────

def simulate_dfa(dfa, lexeme):
    trans_map = {row['state']: row['transitions'] for row in dfa['table']}
    state     = dfa['start_state']
    trace     = [{'state': state, 'action': f"Start in state {state}", 'remaining': lexeme}]

    for i, ch in enumerate(lexeme):
        remaining = lexeme[i + 1:]
        row       = trans_map.get(state, {})
        next_st   = row.get(ch, 'DEAD')

        if state == 'DEAD':
            action = "In DEAD (trap) state — no escape"
        elif next_st == 'DEAD':
            action = f"Read '{ch}' -> DEAD (no transition from {state} on '{ch}')"
        else:
            action = f"Read '{ch}' -> state {next_st}"

        trace.append({'state': next_st, 'action': action, 'remaining': remaining})
        state = next_st

    return trace


# ── REGEX INFO ────────────────────────────────────────────────────────────────

def get_regex_info(tok_type, lexeme):
    if tok_type == 'KEYWORD':
        chain = ' . '.join(f"char('{c}')" for c in lexeme)
        return {
            'regex': lexeme,
            'explanation': f"Keyword '{lexeme}' matched as exact sequence via Thompson concatenation: {chain}. Each character is a 2-state NFA fragment chained by ε-transitions."
        }
    elif tok_type == 'INTEGER':
        return {
            'regex': '[0-9]+',
            'explanation': "One or more decimal digits. Thompson: char_class([0-9]) . star(char_class([0-9])). Minimized DFA: 2 states — q0 (start) → q1 (accept, self-loop on digits). Non-digit → DEAD."
        }
    elif tok_type == 'FLOAT':
        return {
            'regex': '[0-9]+.[0-9]+',
            'explanation': "Digits, a literal dot, then more digits. Thompson: plus([0-9]) . char('.') . plus([0-9]). DFA reads digit-group, dot, then digit-group."
        }
    elif tok_type == 'IDENTIFIER':
        return {
            'regex': '[a-zA-Z_][a-zA-Z0-9_]*',
            'explanation': "A letter/underscore followed by zero or more letters, digits, or underscores. Thompson: char_class([a-zA-Z_]) . star(char_class([a-zA-Z0-9_])). Minimized DFA: 2 states with self-loop on valid tail characters."
        }
    elif tok_type == 'OPERATOR':
        chain = ' . '.join(f"char('{c}')" for c in lexeme)
        return {
            'regex': re.escape(lexeme),
            'explanation': f"Operator '{lexeme}' matched as exact literal. Thompson: {chain}. Any mismatch leads to DEAD."
        }
    elif tok_type == 'SEPARATOR':
        return {
            'regex': re.escape(lexeme),
            'explanation': f"Separator '{lexeme}' matched as single character. Thompson: q0 reads '{lexeme}' → q1 (accept). DEAD state for everything else."
        }
    elif tok_type == 'STRING_LIT':
        return {'regex': '"[^"]*"', 'explanation': 'Opening double-quote, any non-quote characters, closing double-quote.'}
    elif tok_type == 'CHAR_LIT':
        return {'regex': "'.'", 'explanation': "Single-quote, exactly one character, closing single-quote."}
    else:
        return {'regex': '.*', 'explanation': 'Unknown token type.'}


def make_combined_enfa(tok_type):
    return {
        'description': f"Combined master ε-NFA branches via ε-transitions into one sub-machine per token rule. Active machine: {tok_type}.",
        'epsilon_from_master': ['KEYWORD machine', 'FLOAT machine', 'INTEGER machine', 'IDENTIFIER machine'],
        'machines': [],
        'overlap_note': f"Token type: '{tok_type}'. KEYWORD > IDENTIFIER (priority). Maximal Munch: longest match wins.",
    }


# ── TOKENIZER ─────────────────────────────────────────────────────────────────

def tokenize(source):
    tokens = []
    i = 0; line = 1; col = 1

    while i < len(source):
        ch = source[i]; rest = source[i:]

        if ch == '\n':
            line += 1; col = 1; i += 1; continue
        if ch in ' \t\r':
            col += (4 if ch == '\t' else 1); i += 1; continue

        start_col = col

        for op in ['==', '!=', '<=', '>=', '&&', '||']:
            if rest.startswith(op):
                tokens.append({'lexeme': op, 'type': 'OPERATOR', 'line': line, 'col': start_col})
                i += len(op); col += len(op); break
        else:
            m = re.match(r'^[0-9]+\.[0-9]+', rest)
            if m:
                tokens.append({'lexeme': m.group(), 'type': 'FLOAT', 'line': line, 'col': start_col})
                i += len(m.group()); col += len(m.group()); continue

            m = re.match(r'^[0-9]+', rest)
            if m:
                lex = m.group(); after = rest[len(lex):]
                if after and (after[0].isalpha() or after[0] == '_'):
                    bad = re.match(r'^[0-9]+[a-zA-Z_0-9]*', rest)
                    lex = bad.group() if bad else lex
                    tokens.append({'lexeme': lex, 'type': 'ERROR', 'line': line, 'col': start_col})
                else:
                    tokens.append({'lexeme': lex, 'type': 'INTEGER', 'line': line, 'col': start_col})
                i += len(lex); col += len(lex); continue

            m = re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*', rest)
            if m:
                lex = m.group()
                tokens.append({'lexeme': lex, 'type': 'KEYWORD' if lex in KEYWORDS else 'IDENTIFIER', 'line': line, 'col': start_col})
                i += len(lex); col += len(lex); continue

            m = re.match(r'^"[^"]*"', rest)
            if m:
                tokens.append({'lexeme': m.group(), 'type': 'STRING_LIT', 'line': line, 'col': start_col})
                i += len(m.group()); col += len(m.group()); continue

            m_v = re.match(r"^'.'", rest)
            if m_v:
                tokens.append({'lexeme': m_v.group(), 'type': 'CHAR_LIT', 'line': line, 'col': start_col})
                i += len(m_v.group()); col += len(m_v.group()); continue
            m_b = re.match(r"^'[^']*'", rest)
            if m_b:
                tokens.append({'lexeme': m_b.group(), 'type': 'ERROR', 'line': line, 'col': start_col})
                i += len(m_b.group()); col += len(m_b.group()); continue

            if ch in '=+-*/<>!%':
                tokens.append({'lexeme': ch, 'type': 'OPERATOR', 'line': line, 'col': start_col})
                i += 1; col += 1; continue

            if ch in '(){};,[]':
                tokens.append({'lexeme': ch, 'type': 'SEPARATOR', 'line': line, 'col': start_col})
                i += 1; col += 1; continue

            tokens.append({'lexeme': ch, 'type': 'ERROR', 'line': line, 'col': start_col})
            i += 1; col += 1
            continue

        if rest[:2] in ['==', '!=', '<=', '>=', '&&', '||']:
            continue

    return tokens


# ── PROCESS ONE TOKEN ─────────────────────────────────────────────────────────

def process_token(tok):
    lexeme   = tok['lexeme']
    tok_type = tok['type']

    result = {
        'token': tok, 'accepted': False, 'error': None,
        'regex': '', 'regex_explanation': '',
        'enfa': None, 'combined_enfa': None, 'nfa': None, 'dfa': None, 'trace': [],
    }

    if tok_type in ('ERROR', 'UNKNOWN'):
        if re.match(r'^[0-9]', lexeme):
            result['error'] = f"Invalid token '{lexeme}': identifiers cannot start with a digit. Rule: [a-zA-Z_][a-zA-Z0-9_]*"
        elif lexeme.startswith("'"):
            result['error'] = f"Invalid char literal '{lexeme}': must contain exactly one character."
        else:
            result['error'] = f"Unrecognized token '{lexeme}'"
        return result

    ri = get_regex_info(tok_type, lexeme)
    result['regex']             = ri['regex']
    result['regex_explanation'] = ri['explanation']

    # Pipeline: Regex → ε-NFA (Thompson) → NFA → DFA → simulate
    t   = Thompson()
    nfa = build_token_nfa(t, tok_type, lexeme)   # builds ε-NFA

    enfa_states = enfa_to_dict(nfa)
    enfa_syms   = sorted({sym for s in enfa_states for sym in s['transitions'].keys()})
    result['enfa'] = {'states': enfa_states, 'regex': ri['regex'], 'symbols': enfa_syms}
    result['combined_enfa'] = make_combined_enfa(tok_type)
    result['nfa']           = build_nfa_table(nfa)   # ε-NFA → NFA

    dfa = build_dfa(nfa)                              # NFA → DFA
    result['dfa'] = dfa

    trace = simulate_dfa(dfa, lexeme)                 # run source on DFA → tokens
    result['trace'] = trace

    final_state        = trace[-1]['state'] if trace else dfa['start_state']
    result['accepted'] = final_state in dfa['accept_states']
    if not result['accepted']:
        result['error'] = f"DFA rejects '{lexeme}': ended in non-accepting state '{final_state}'."

    return result


# ── PUBLIC API ────────────────────────────────────────────────────────────────

def analyze(source):
    tokens  = tokenize(source)
    results = [process_token(tok) for tok in tokens]
    overall = 'ACCEPTED' if all(r['accepted'] for r in results) else 'REJECTED'
    return {'source': source, 'overall': overall, 'tokens': results}