from bokeh.plotting import curdoc, figure
from bokeh.models import (ColumnDataSource,
                          HoverTool,
                          Span,
                          LabelSet,
                          LinearColorMapper,
                          FactorRange,
                          ColorBar,
                          Div)
from bokeh.models.widgets import DateRangeSlider, CheckboxButtonGroup
from bokeh.transform import transform
from bokeh.palettes import Viridis11
from bokeh.layouts import layout, widgetbox, row
from db import get_offense_data, get_available_districts, get_available_months, get_top10_groups, \
    get_heatmap_data
from statistics import mean

RED = "#e26855"

months = get_available_months()
districts = get_available_districts()

selected_months = DateRangeSlider(start=months[0],
                                  end=months[-1],
                                  value=(months[0], months[-1]),
                                  step=1,
                                  callback_policy="mouseup")

selected_districts = CheckboxButtonGroup(labels=list(districts), active=list(range(len(districts))))

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

heatmap_source = ColumnDataSource(dict(DAY_OF_WEEK=[], HOUR=[], counts=[]))

day_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
hours = [str(x) for x in range(0, 24)]
mapper = LinearColorMapper(palette=Viridis11)

heatmap = figure(title="Number of Offenses per Hour and Day Of Week", x_range=day_of_week,
                 y_range=hours, tools="hover")
heatmap.hover.tooltips = [("Day of Week", "@DAY_OF_WEEK"),
                          ("Hour of Day", "@HOUR"),
                          ("Number of Offenses", "@counts")]
heatmap.rect(x='DAY_OF_WEEK', y='HOUR', source=heatmap_source, width=1, height=1,
             fill_color=transform('counts', mapper), line_color=None)

labels = LabelSet(x="DAY_OF_WEEK", y="HOUR", text="counts", source=heatmap_source,
                  text_font_size='1em', x_offset=-10, y_offset=-10)

colorbar = ColorBar(color_mapper=mapper, location=(0, 0))
colorbar.major_label_text_align = 'left'

heatmap.add_layout(labels)
heatmap.add_layout(colorbar, "right")

heatmap.axis.axis_line_color = None
heatmap.axis.major_tick_line_color = None
heatmap.axis.major_label_text_font_size = "8pt"
heatmap.axis.major_label_standoff = 0


def update_top10():
    start_date, end_date = selected_months.value_as_date
    data = get_top10_groups(start_date,
                            end_date,
                            [districts[i] for i in selected_districts.active]).sort_values('counts', ascending=True)
    top10_source.data = data
    top10_yrange.factors = data.code_group.to_list()


def update_heatmap():
    start_date, end_date = selected_months.value_as_date
    data = get_heatmap_data(start_date, end_date, [districts[i] for i in selected_districts.active])
    heatmap_source.data = data
    mapper.low = data.counts.min()
    mapper.high = data.counts.max()


def update_line():
    start_date, end_date = selected_months.value_as_date

    data = get_offense_data(start_date,
                            end_date,
                            [districts[i] for i in selected_districts.active])

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


def update_graphs():
    update_heatmap()
    update_top10()
    update_line()


selected_months.on_change('value_throttled', lambda attr, old, new: update_graphs())
selected_districts.on_change('active', lambda attr, old, new: update_graphs())
line_source.selected.on_change('indices', lambda attr, old, new: update_selection())

update_graphs()

controls = row(widgetbox(selected_months), widgetbox(selected_districts), sizing_mode='stretch_width')

curdoc().add_root(controls)

curdoc().add_root(layout([
    [num_offenses, num_shootings],
    [top10, heatmap]
], sizing_mode='stretch_width'))
