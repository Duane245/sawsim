"""README figure: (a) TC-SAW admittance, SawSim vs reference; (b) fr/fa deviation of all nine templates.

Writes docs/figures/readme_validation_{light,dark}.png. Run from the repo root: python docs/figures/make_readme_figure.py
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from sawsim.metrics import resonances

THEMES = {
    'light': dict(surface='#fcfcfb', ink='#0b0b0b', ink2='#52514e', muted='#8a8984', grid='#e7e6e2',
                  band='#efeeea', s1='#2a78d6', s2='#eb6834', ref='#52514e'),
    'dark': dict(surface='#1a1a19', ink='#ffffff', ink2='#c3c2b7', muted='#8f8e86', grid='#33332f',
                 band='#2a2a27', s1='#3987e5', s2='#d95926', ref='#c3c2b7'),
}
TEMPLATES = [('sp_single_layer', '2D single layer'), ('sp_double_layer', '2D LT / Si'),
             ('sp_triple_layer', '2D three layers'), ('sp_quad_layer', '2D IHP-SAW (4 layers)'),
             ('sp_tcsaw', '2D TC-SAW'), ('sp_2p5d_single_layer', '2.5D single layer'),
             ('sp_2p5d_double_layer', '2.5D LT / Si'), ('sp_2p5d_triple_layer', '2.5D three layers'),
             ('sp_2p5d_quad_layer', '2.5D IHP-SAW (4 layers)')]

rows = []
for mid, name in TEMPLATES:
    z = np.load('tests/data/%s.npz' % mid)
    r, s = resonances(z['frequency_hz'], z['reference_magnitude']), resonances(z['frequency_hz'], z['sawsim_magnitude'])
    rows.append((name, (s['fr_ghz'] - r['fr_ghz']) * 1e3, (s['fa_ghz'] - r['fa_ghz']) * 1e3))
tc = np.load('tests/data/sp_tcsaw.npz')
f = tc['frequency_hz'] * 1e-9
r_tc, s_tc = resonances(tc['frequency_hz'], tc['reference_magnitude']), resonances(tc['frequency_hz'], tc['sawsim_magnitude'])


def draw(theme):
    c = THEMES[theme]
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'text.color': c['ink'],
                         'axes.labelcolor': c['ink2'], 'xtick.color': c['ink2'], 'ytick.color': c['ink2']})
    fig = plt.figure(figsize=(11, 4.5), dpi=200, facecolor=c['surface'])
    gs = fig.add_gridspec(1, 2, width_ratios=[1.55, 1], wspace=0.42, left=0.065, right=0.985, top=0.80, bottom=0.13)
    ax, bx = fig.add_subplot(gs[0]), fig.add_subplot(gs[1])
    for a in (ax, bx):
        a.set_facecolor(c['surface'])
        for side in ('top', 'right'):
            a.spines[side].set_visible(False)
        for side in ('left', 'bottom'):
            a.spines[side].set_color(c['muted'])
        a.tick_params(length=3, color=c['muted'])

    # (a) admittance
    ax.semilogy(f, tc['sawsim_magnitude'], color=c['s1'], lw=2.0, zorder=3, solid_capstyle='round')
    step = 4
    ax.semilogy(f[::step], tc['reference_magnitude'][::step], ls='none', marker='o', ms=4.6, mfc=c['surface'],
                mec=c['ref'], mew=1.1, zorder=4)
    ax.grid(True, which='major', color=c['grid'], lw=0.8)
    ax.set_xlim(f[0], f[-1])
    ax.set_xlabel('Frequency (GHz)')
    ax.set_ylabel('|Y| (S/m)')
    for key, side in (('fr', -1), ('fa', 1)):
        x = s_tc[key + '_ghz']
        d = round((x - r_tc[key + '_ghz']) * 1e3, 2) + 0.0
        ax.axvline(x, color=c['muted'], lw=0.8, ls=(0, (2, 2)), zorder=1)
        ax.annotate(('%s  %.4f GHz\nΔ %.2f MHz' % (key, x, d)).replace('-', '−'), xy=(x, 0.98), xycoords=('data', 'axes fraction'),
                    xytext=(7 * side, 0), textcoords='offset points', ha='left' if side > 0 else 'right', va='top',
                    fontsize=8.6, color=c['ink2'], linespacing=1.35)
    ax.legend(handles=[Line2D([], [], color=c['s1'], lw=2, label='SawSim'),
                       Line2D([], [], ls='none', marker='o', ms=5, mfc=c['surface'], mec=c['ref'], mew=1.1,
                              label='Reference FEM')],
              loc='lower right', frameon=False, fontsize=9, labelcolor=c['ink2'])
    ax.set_title('TC-SAW unit cell  ·  LiNbO₃ / Cu / SiO₂ / SiN', loc='left', fontsize=10.5, color=c['ink'], pad=8)

    # (b) fr/fa deviation dot plot
    y = np.arange(len(rows))[::-1]
    bx.axvspan(-0.5, 0.5, color=c['band'], zorder=0, lw=0)
    bx.axvline(0, color=c['muted'], lw=0.9, zorder=1)
    bx.scatter([r[1] for r in rows], y + 0.14, s=46, marker='o', color=c['s1'], edgecolors=c['surface'], linewidths=1.2,
               zorder=3, label='Δfr')
    bx.scatter([r[2] for r in rows], y - 0.14, s=50, marker='D', color=c['s2'], edgecolors=c['surface'], linewidths=1.2,
               zorder=3, label='Δfa')
    bx.set_yticks(y)
    bx.set_yticklabels([r[0] for r in rows], fontsize=8.8)
    bx.tick_params(axis='y', length=0)
    bx.spines['left'].set_visible(False)
    bx.set_xlim(-0.75, 0.75)
    bx.set_ylim(-0.7, len(rows) - 0.3)
    bx.set_xticks([-0.5, -0.25, 0, 0.25, 0.5])
    bx.set_xlabel('Deviation from reference (MHz)')
    bx.grid(True, axis='x', color=c['grid'], lw=0.8, zorder=0)
    from matplotlib.patches import Patch
    h, l = bx.get_legend_handles_labels()
    bx.legend(h + [Patch(facecolor=c['band'], edgecolor=c['muted'], lw=0.6)], l + ['±0.5 MHz'], loc='upper left',
              frameon=False, fontsize=9, labelcolor=c['ink2'], handletextpad=0.4, borderaxespad=0.2)
    bx.set_title('Resonance & anti-resonance, all templates', loc='left', fontsize=10.5, color=c['ink'], pad=8)

    fig.text(0.065, 0.955, 'SawSim against an independent reference FEM', fontsize=13, fontweight='bold', color=c['ink'])
    fig.text(0.065, 0.905, 'fr and fa of all nine unit-cell templates agree within 0.5 MHz – most within 0.1 MHz',
             fontsize=9.6, color=c['ink2'])
    out = 'docs/figures/readme_validation_%s.png' % theme
    fig.savefig(out, facecolor=c['surface'])
    plt.close(fig)
    return out


for t in THEMES:
    print(draw(t))
