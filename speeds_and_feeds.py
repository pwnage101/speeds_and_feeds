#!/usr/bin/env python3

from collections import OrderedDict
from fractions import Fraction
from math import pi
import numpy as np
import pint

import matplotlib
matplotlib.use('PDF')
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt

ureg = pint.UnitRegistry()
ureg.define('revolution = 6.2831853 * radian = rev')

# Maximum axial DOC on the X axis as a multiple of tool diameter.  Set to 2 or
# 3 for substantial utilization of the side of the endmill.  That's rare, so
# for the purposes of readability use 1.5:
MAX_DOC_AXIAL = 1.5

# Define your tools here.
tools = [
    {
        'diameter': 3/4 * ureg.inch,
        'tooth_count': 4,
        'material': 'HSS',
    },
    {
        'diameter': 3/8 * ureg.inch,
        'tooth_count': 2,
        'material': 'HSS',
    },
    {
        'diameter': 3/8 * ureg.inch,
        'tooth_count': 2,
        'material': 'Carbide',
    },
    {
        'diameter': 3/16 * ureg.inch,
        'tooth_count': 2,
        'material': 'Carbide',
    },
]

materials = OrderedDict([
    ('Aluminum', {
        'SFM': 300 * (ureg.ft / ureg.min),
        'unit_power': 0.4 * (ureg.hp / (ureg.inch**3 / ureg.min)),
    }),
    ('Mild Steel', {
        'SFM': 100 * (ureg.ft / ureg.min),
        'unit_power': 1.8 * (ureg.hp / (ureg.inch**3 / ureg.min)),
    }),
    ('4130 Steel', {
        'SFM': 80 * (ureg.ft / ureg.min),
        'unit_power': 2.2 * (ureg.hp / (ureg.inch**3 / ureg.min)),
    }),
    ('4140 Steel, annealed', {
        'SFM': 60 * (ureg.ft / ureg.min),
        'unit_power': 2.2 * (ureg.hp / (ureg.inch**3 / ureg.min)),
    }),
    ('4140 Steel, hardened', {
        'SFM': 30 * (ureg.ft / ureg.min),
        'unit_power': 2.6 * (ureg.hp / (ureg.inch**3 / ureg.min)),
    }),
])

# machine properties
machine_horsepower = 0.5 * ureg.hp  # about half of the motor's rated horsepower
machine_efficiency = 0.75  # dimensionless fraction
machine_speed_max = 2500 * ureg.rev / ureg.min
machine_feed_max = 60 * ureg.inch / ureg.min

with PdfPages('speeds_and_feeds.pdf') as pdf:
    for tool in tools:
        # X axis values
        doc_axial = np.arange(0.0, MAX_DOC_AXIAL * tool['diameter'].to(ureg.inch).magnitude + 0.01, 0.01) * ureg.inch

        fig, ax = plt.subplots(figsize=(9, 8))

        for material_name, material_properties in materials.items():
            SFM = material_properties['SFM']

            # For simplicity, we say carbide tools can sustain double the SFM
            # of HSS tools.  In reality, this varies widely with different
            # material types and tool coatings, but 2x surface speed is a good
            # conservative estimate.  In production environments, some people
            # are running carbide 4-5x.
            if tool['material'] is 'Carbide':
                SFM *= 2.0

            speed = SFM / ( pi * tool['diameter'] / ureg.rev )

            if speed > machine_speed_max:
                speed = machine_speed_max

            feed = 0.005 * tool['diameter'] * speed * (tool['tooth_count'] / ureg.rev)

            if feed > machine_feed_max:
                feed = machine_feed_max

            MRR = machine_horsepower * machine_efficiency / material_properties['unit_power']
            doc_radial = MRR / feed / doc_axial
            stepover = 100 * (doc_radial / tool['diameter']).to(ureg.dimensionless)

            ax.plot(doc_axial, stepover, label='{}: {:.0f} RPM, {:.1f} IPM'.format(
                material_name,
                speed.to(ureg.rev / ureg.min).magnitude,
                feed.to(ureg.inch / ureg.min).magnitude,
                ))

        ax.legend()

        ax.set(xlabel='DOC, Axial (inch)', ylabel='Stepover (%)',
               title='Milling Parameters, {:.2f} hp, {}" {:d} fl. {} End Mill'.format(
                   machine_horsepower.magnitude,
                   Fraction(tool['diameter'].magnitude).limit_denominator(),
                   int(tool['tooth_count']),
                   tool['material'],
                   ))

        # X limits are proportional to tool diameter.
        ax.set_xlim(0, MAX_DOC_AXIAL * tool['diameter'].to(ureg.inch).magnitude)

        # Do some magic to get perfect x axis tick granularity.
        tick_step = 0.0001
        for _ in range(10):
            if tick_step*10 > ax.get_xlim()[1]/8:
                tick_step *= 5
                break
            if tick_step*20 > ax.get_xlim()[1]/8:
                tick_step *= 10
                break
            if tick_step*50 > ax.get_xlim()[1]/8:
                tick_step *= 20
                break
            tick_step *= 10
        ax.set_xticks(np.arange(0, ax.get_xlim()[1], tick_step))

        # Limit display up to 100% stepover since that's the entire diameter of
        # the endmill (slot milling).
        ax.set_ylim(0, 100)
        ax.set_yticks(np.arange(0, 101, step=5))

        ax.grid()

        # Setup secondary axis on right side of graph to show physical stepover.
        ax2 = ax.twinx()
        ax2.set_ylim(0, tool['diameter'].magnitude)
        yticks = np.arange(0, tool['diameter'].magnitude*1.05, step=tool['diameter'].magnitude*0.05)
        ax2.set_yticks(yticks)
        ax2.set_yticklabels([
            '{:.3f} [{:.2f}]'.format(
                tick,
                (tick * ureg.inch).to(ureg.mm).magnitude
            ) for tick in yticks])
        ax2.set_ylabel('Physical Stepover (inch [mm])')

        fig.tight_layout()  # otherwise the right y-label is slightly clipped
        pdf.savefig(fig)
