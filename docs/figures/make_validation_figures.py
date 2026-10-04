"""Validation figures: |Y| of every template, SawSim against the reference FEM solution, with fr/fa deviations.

Writes docs/figures/validation_2d.png (five 2D templates) and docs/figures/validation_2p5d.png (four 2.5D templates)
from tests/data. Run from the repo root: python docs/figures/make_validation_figures.py
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from sawsim.metrics import resonances

C = dict(surface='#fcfcfb', ink='#0b0b0b', ink2='#52514e', muted='#8a8984', grid='#e7e6e2', sim='#2a78d6', ref='#d0461e')

GROUPS = {
    'validation_2d.png': ('2D unit cells (|Y| per unit aperture)', 'S/m', [
        ('sp_single_layer', 'Single layer', 'LiTaO₃'),
        ('sp_double_layer', 'Double layer', 'LiTaO₃ / Si'),
        ('sp_triple_layer', 'Three layers', 'LiTaO₃ / SiO₂ / poly-Si'),
        ('sp_quad_layer', 'IHP-SAW (4 layers)', 'LiTaO₃ / SiO₂ / poly-Si / Si'),
        ('sp_tcsaw', 'TC-SAW', 'LiNbO₃ with SiO₂ / SiN overcoat'),
    ]),
    'validation_2p5d.png': ('2.5D Hex27 slices (total slice |Y|)', 'S', [
        ('sp_2p5d_single_layer', 'Single layer', 'LiTaO₃'),
        ('sp_2p5d_double_layer', 'Double layer', 'LiTaO₃ / Si'),
        ('sp_2p5d_triple_layer', 'Three layers', 'LiTaO₃ / SiO₂ / poly-Si'),
        ('sp_2p5d_quad_layer', 'IHP-SAW (4 layers)', 'LiTaO₃ / SiO₂ / poly-Si / Si'),
    ]),
}


def panel(ax, model, name, stack, unit):
    z = np.load('tests/data/%s.npz' % model)
    f = z['frequency_hz'] * 1e-9
    ref, sim = z['reference_magnitude'], z['sawsim_magnitude']
    r, s = resonances(z['frequency_hz'], ref), resonances(z['frequency_hz'], sim)
    ax.semilogy(f, ref, color=C['ref'], lw=2.6, solid_capstyle='round')
    ax.semilogy(f, sim, color=C['sim'], lw=1.4, ls=(0, (4, 2)))
    for x in (r['fr_ghz'], r['fa_ghz']):
        ax.axvline(x, color=C['muted'], lw=0.8, ls=':', zorder=0)
    dfr, dfa = (s['fr_ghz'] - r['fr_ghz']) * 1e3, (s['fa_ghz'] - r['fa_ghz']) * 1e3
    ax.text(0.98, 0.04, 'fr %.4f GHz   Δfr %+.2f MHz\nfa %.4f GHz   Δfa %+.2f MHz'
            % (r['fr_ghz'], dfr + 0.0, r['fa_ghz'], dfa + 0.0),
            transform=ax.transAxes, ha='right', va='bottom', fontsize=9, color=C['ink2'], family='DejaVu Sans Mono',
            bbox=dict(boxstyle='round,pad=0.35', fc=C['surface'], ec=C['grid']))
    ax.set_title(name, loc='left', fontsize=12, color=C['ink'], fontweight='bold', pad=18)
    ax.text(0, 1.02, stack, transform=ax.transAxes, fontsize=9.5, color=C['ink2'], va='bottom')
    ax.set_xlim(f[0], f[-1])
    ax.set_xlabel('Frequency (GHz)')
    ax.set_ylabel('|Y| (%s)' % unit)
    ax.grid(True, which='major', color=C['grid'], lw=0.8)
    ax.set_facecolor(C['surface'])
    for side in ('top', 'right'):
        ax.spines[side].set_visible(False)
    for side in ('left', 'bottom'):
        ax.spines[side].set_color(C['muted'])


def figure(fname, title, unit, cases):
    rows = (len(cases) + 1) // 2
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'axes.labelcolor': C['ink2'],
                         'xtick.color': C['ink2'], 'ytick.color': C['ink2']})
    fig, axs = plt.subplots(rows, 2, figsize=(12, 3.9 * rows + 0.9), dpi=160, facecolor=C['surface'])
    axs = axs.ravel()
    for ax, case in zip(axs, cases):
        panel(ax, *case, unit)
    handles = [Line2D([], [], color=C['ref'], lw=2.6, label='Reference FEM'),
               Line2D([], [], color=C['sim'], lw=1.4, ls=(0, (4, 2)), label='SawSim'),
               Line2D([], [], color=C['muted'], lw=0.8, ls=':', label='Reference fr / fa')]
    if len(cases) < len(axs):
        axs[-1].axis('off')
        axs[-1].legend(handles=handles, loc='center', frameon=False, fontsize=12)
    else:
        fig.legend(handles=handles, loc='upper right', ncol=3, frameon=False, fontsize=10.5, bbox_to_anchor=(0.99, 0.995))
    fig.suptitle(title, x=0.01, ha='left', fontsize=14, fontweight='bold', color=C['ink'])
    fig.tight_layout(rect=(0, 0, 1, 0.975), h_pad=2.2, w_pad=2.5)
    fig.savefig('docs/figures/' + fname, facecolor=C['surface'])
    plt.close(fig)


for fname, (title, unit, cases) in GROUPS.items():
    figure(fname, title, unit, cases)
    print('wrote docs/figures/' + fname)
