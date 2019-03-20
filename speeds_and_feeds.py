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
        'diameter': 2.0 * ureg.inch,
        'tooth_count': 1,
        'material': 'HSS/Cobalt',
    },
    {
        'diameter': 3/4 * ureg.inch,
        'tooth_count': 4,
        'material': 'HSS/Cobalt',
    },
    {
        'diameter': 5/8 * ureg.inch,
        'tooth_count': 4,
        'material': 'HSS/Cobalt',
    },
    {
        'diameter': 1/2 * ureg.inch,
        'tooth_count': 4,
        'material': 'HSS/Cobalt',
    },
    {
        'diameter': 1/2 * ureg.inch,
        'tooth_count': 4,
        'material': 'Carbide',
    },
    {
        'diameter': 3/8 * ureg.inch,
        'tooth_count': 4,
        'material': 'Carbide',
    },
    {
        'diameter': 3/8 * ureg.inch,
        'tooth_count': 2,
        'material': 'HSS/Cobalt',
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

# Define all the materials which are relevant to you.
materials = OrderedDict([
    ('Aluminum', {
        'SFM': 300 * (ureg.ft / ureg.min),
        'unit_power': 0.4 * (ureg.hp / (ureg.inch**3 / ureg.min)),
        'color': 'xkcd:blue',
        'linestyle': '-',
        'linewidth': 1.5,
    }),
    ('Mild Steel', {
        'SFM': 100 * (ureg.ft / ureg.min),
        'unit_power': 1.8 * (ureg.hp / (ureg.inch**3 / ureg.min)),
        'color': 'xkcd:red',
        'linestyle': '-',
        'linewidth': 1.5,
    }),
    ('4130 Steel', {
        'SFM': 80 * (ureg.ft / ureg.min),
        'unit_power': 2.2 * (ureg.hp / (ureg.inch**3 / ureg.min)),
        'color': 'xkcd:blue',
        'linestyle': '--',
        'linewidth': 2.0,
    }),
    ('4140 Steel, annealed', {
        'SFM': 60 * (ureg.ft / ureg.min),
        'unit_power': 2.3 * (ureg.hp / (ureg.inch**3 / ureg.min)),
        'color': 'xkcd:red',
        'linestyle': '--',
        'linewidth': 1.5,
    }),
    ('4140 Steel, hardened', {
        'SFM': 30 * (ureg.ft / ureg.min),
        'unit_power': 2.6 * (ureg.hp / (ureg.inch**3 / ureg.min)),
        'color': 'xkcd:green',
        'linestyle': '--',
        'linewidth': 1.5,
    }),
    ('304 Stainless', {
        'SFM': 50 * (ureg.ft / ureg.min),
        'unit_power': 1.8 * (ureg.hp / (ureg.inch**3 / ureg.min)),
        'color': 'xkcd:black',
        'linestyle': '-.',
        'linewidth': 1.5,
    }),
])

# This multiplier gives us our safety buffer.  We're trying to operate the
# machine below the max ratings, so any calculation errors due to poor
# approximations won't overload the motor and cause stalls/breakages or reduce
# machine/tool lifespan.
machine_horsepower_multiplier = 0.5

# This number represents the faction of the power transmitted to the tool
# (milling) or part (turning).  The machine's transmission isn't ideal; there
# are always friction losses inside the motor, belt, spindle bearings, and
# other miscellaneous things such as the tailstock bearings and power feed
# gears/screws.
machine_efficiency = 0.75

machines = [
    {
        'name': 'Sharp LMV CNC Mill',
        'horsepower': 3.0 * ureg.hp,
        'feed_max': 60 * ureg.inch / ureg.min,
        'vari_speed_max': 3000 * ureg.rev / ureg.min,
    },
    {
        'name': 'Bridgeport J-Head Mill',
        'horsepower': 1.0 * ureg.hp,
        'feed_max': 30 * ureg.inch / ureg.min,
        'speeds': [80, 135, 210, 325, 660, 1115, 1750, 2720] * ureg.rev / ureg.min,
    },
]

def closest_machine_speed(speed, machine):
    """
    For a given ideal spindle speed, return the nearest one which is physically
    possible.
    """
    if 'speeds' in machine:
        return min(machine['speeds'], key=lambda x: abs(x-speed))
    else:
        if speed > machine['vari_speed_max']:
            return machine['vari_speed_max']
        else:
            return speed

for machine in machines:

    machine_filename_suffix = machine['name'].replace(' ', '_')

    with PdfPages('speeds_and_feeds_{}.pdf'.format(machine_filename_suffix)) as pdf:

        # Add a new graph on a new page for each different tool.
        for tool in tools:
            # X axis values
            doc_axial = np.arange(0.0, MAX_DOC_AXIAL * tool['diameter'].to(ureg.inch).magnitude + 0.01, 0.01) * ureg.inch

            fig, ax = plt.subplots(figsize=(11.0, 8.0))

            # Add vertical line which represents 1D axial DOC for visual
            # reference.
            #ax.axvline(tool['diameter'].to(ureg.inch).magnitude, color='black', linestyle='--', linewidth=1.0)
            ax_top = ax.twiny()
            ax_top.set_xlim(0, MAX_DOC_AXIAL * tool['diameter'].to(ureg.inch).magnitude)
            ax_top.set_xticks([tool['diameter'].to(ureg.inch).magnitude, 1.5 * tool['diameter'].to(ureg.inch).magnitude])
            ax_top.set_xticklabels(['1D', '1.5D'])

            # Plot a new line for each different type of material.
            for material_name, material_properties in materials.items():
                SFM = material_properties['SFM']

                # For simplicity, we say carbide tools can sustain double the SFM
                # of HSS tools.  In reality, this varies widely with different
                # material types and tool coatings, but 2x surface speed is a good
                # conservative estimate.  In production environments, some people
                # are running carbide 4-5x.
                if tool['material'] is 'Carbide':
                    SFM *= 2.5

                speed = SFM / ( pi * tool['diameter'] / ureg.rev )
                speed = closest_machine_speed(speed, machine)

                feed = 0.005 * tool['diameter'] * speed * (tool['tooth_count'] / ureg.rev)
                if feed > machine['feed_max']:
                    feed = machine['feed_max']

                target_spindle_horsepower = machine['horsepower'] * machine_horsepower_multiplier * machine_efficiency
                MRR = target_spindle_horsepower / material_properties['unit_power']
                doc_radial = MRR / feed / doc_axial
                stepover = 100 * (doc_radial / tool['diameter']).to(ureg.dimensionless)

                ax.plot(
                    doc_axial,
                    stepover,
                    label='{}: {:.0f} RPM, {:.0f} IPM'.format(
                        material_name,
                        speed.to(ureg.rev / ureg.min).magnitude,
                        feed.to(ureg.inch / ureg.min).magnitude,
                    ),
                    color=material_properties['color'],
                    linestyle=material_properties['linestyle'],
                    linewidth=material_properties['linewidth'],
                )

            ax.legend()

            ax.set(xlabel='Axial DOC (inch [mm])', ylabel='Max Stepover (%)')
            ax.set_title(
                'Rough Milling  •  {} {:.1f} hp, {:.0f}% load  •  {}" {:d} fl. {} End Mill'.format(
                    machine['name'],
                    machine['horsepower'].magnitude,
                    machine_horsepower_multiplier * 100,
                    Fraction(tool['diameter'].magnitude).limit_denominator(),
                    int(tool['tooth_count']),
                    tool['material'],
                ),
                y=1.05, # this just manually places the title to not overlap with the top ticks.
            )

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
            xticks = np.arange(0, ax.get_xlim()[1], tick_step)
            ax.set_xticks(xticks)
            ax.set_xticklabels([
                '{:.3f}\n[{:.2f}]'.format(tick, (tick * ureg.inch).to(ureg.mm).magnitude)
                for tick in xticks
            ])
            # Limit display up to 100% stepover since that's the entire diameter of
            # the endmill (i.e. slot milling).
            ax.set_ylim(0, 100)
            ax.set_yticks(np.arange(0, 101, step=5))

            ax.grid()

            # Setup secondary axis on right side of graph to show physical stepover.
            ax_right = ax.twinx()
            ax_right.set_ylim(0, tool['diameter'].magnitude)
            yticks = np.arange(0, tool['diameter'].magnitude*1.05, step=tool['diameter'].magnitude*0.05)
            ax_right.set_yticks(yticks)
            ax_right.set_yticklabels([
                '{:.3f} [{:.2f}]'.format(
                    tick,
                    (tick * ureg.inch).to(ureg.mm).magnitude
                ) for tick in yticks])
            ax_right.set_ylabel('Radial DOC (inch [mm])')

            fig.tight_layout()  # otherwise the right y-label is slightly clipped
            pdf.savefig(fig)
