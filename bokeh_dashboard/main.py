from bokeh.plotting import curdoc, figure
from bokeh.models import (ColumnDataSource,
                          HoverTool,
                          Span,
                          BoxSelectTool,
                          LabelSet,
                          LinearColorMapper,
                          FactorRange)
from bokeh.models.widgets import DateRangeSlider, MultiSelect, DateSlider
from bokeh.transform import transform
from bokeh.palettes import Viridis11
from bokeh.layouts import row, layout
import pandas as pd
from db import get_offense_data, get_available_districts, get_available_months, get_top10_groups
from statistics import mean

RED = "#e26855"

months = get_available_months()
districts = get_available_districts()

selected_months = DateRangeSlider(start=months[0],
                                  end=months[-1],
                                  value=(months[0], months[-1]),
                                  step=1,
                                  callback_policy="mouseup")

selected_districts = MultiSelect(title="Select districts",
                                 value=list(districts),
                                 options=[(name, name) for name in districts],
                                 size=10)

line_source = ColumnDataSource(data=dict(num_shootings=[], num_offenses=[], year_month=[]))

tools = ["xbox_select", "pan", "wheel_zoom", "save", "reset"]

offenses_tooltip = HoverTool(
    tooltips=[('Date', '@year_month{%b %Y}'),
              ('Number of Offenses', '@num_offenses')],
    formatters={'year_month': 'datetime'},
    mode="vline"
)

num_offenses = figure(x_axis_type="datetime",
                      title="Number of Offenses per Month",
                      tools=tools,
                      active_drag="xbox_select")
num_offenses.line(x='year_month', y='num_offenses', source=line_source, color=RED, line_width=1.5)
num_offenses.add_tools(offenses_tooltip)
num_offenses.circle(x='year_month', y='num_offenses', source=line_source, color="black", size=4)
num_offenses.yaxis.axis_label = 'Number of Offenses'
num_offenses.xaxis.axis_label = 'Date'

mean_line = Span(location=0,
                 dimension='width',
                 line_color=RED,
                 line_dash=[8, 3])

num_offenses.add_layout(mean_line)

shootings_tooltip = HoverTool(
    tooltips=[('Date', '@year_month{%b %Y}'),
              ('Number of Shootings', '@num_shootings')],
    formatters={'year_month': 'datetime'},
    mode="vline"
)

num_shootings = figure(x_axis_type="datetime",
                       title="Number of Shootings per Month",
                       active_drag="xbox_select",
                       tools=tools)
num_shootings.add_tools(shootings_tooltip)
num_shootings.line(x='year_month', y='num_shootings', source=line_source, color=RED, line_width=1.5)
num_shootings.circle(x='year_month', y='num_shootings', source=line_source, color="black", size=4)

mean_shootings = Span(location=0,
                      dimension="width",
                      line_color=RED,
                      line_dash=[8, 3])

num_shootings.add_layout(mean_shootings)
num_shootings.x_range = num_offenses.x_range

top10_source = ColumnDataSource(data=dict(code_group=[], counts=[]))

top10_yrange = FactorRange(factors=[])
top10 = figure(title="Top 10 Offence Code Groups", y_range=top10_yrange, plot_width=600)
top10.hbar(right="counts",
           y="code_group",
           height=0.8,
           source=top10_source)
labels = LabelSet(x="counts",
                  y="code_group",
                  text="counts",
                  source=top10_source,
                  x_offset=5,
                  y_offset=-10,
                  text_font_size='1em')

top10.add_layout(labels)


def update_top10():
    start_date, end_date = selected_months.value_as_date
    data = get_top10_groups(start_date,
                            end_date,
                            selected_districts.value).sort_values('counts', ascending=True)
    top10_source.data = data
    top10_yrange.factors = data.code_group.to_list()


def update_line():
    start_date, end_date = selected_months.value_as_date
    data = get_offense_data(start_date,
                            end_date,
                            selected_districts.value)

    line_source.data = data
    mean_line.location = data.num_offenses.mean()
    mean_shootings.location = data.num_shootings.mean()


def update_selection():
    selected = line_source.selected.indices

    if selected:
        num_shootings = [line_source.data["num_shootings"][i] for i in selected]
        num_offenses = [line_source.data["num_offenses"][i] for i in selected]
        mean_line.location = mean(num_offenses)
        mean_shootings.location = mean(num_shootings)


selected_months.on_change('value_throttled', lambda attr, old, new: update_line())
selected_districts.on_change('value', lambda attr, old, new: update_line())
line_source.selected.on_change('indices', lambda attr, old, new: update_selection())

update_line()
update_top10()

curdoc().add_root(layout([
    [selected_months, selected_districts],
    [num_offenses, num_shootings],
    [top10]
]))
