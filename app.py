"""
Web app to
"""
import json
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


from flask import Flask, request, render_template
from StringIO import StringIO

app = Flask(__name__)

SURVEY_DATA = pd.read_csv("fake_2cnty_2q.csv")

QUESTION_KEY = json.loads(open('question_key.json', 'r').read())


@app.route('/')
def hello():
    """splashy"""
    return "<a href='/results'>MAKE A SOME BAR CHARTS!!!!</a>"

QUESTIONS = ["Pigs Rule!", "I like ice cream"]


@app.route('/results', methods=['GET'])
def show_results():
    """
    Show frequencies of responses to the questions.
    """
    req_keys = request.args.keys()

    counties = SURVEY_DATA.county.copy()  # + ["All"]

    counties.sort()
    counties = ["All"] + list(counties.unique())

    county = request.args['county'] if 'county' in req_keys else "All"
    county_idx = counties.index(county)

    if county_idx == 0:
        prev_county = None
        next_county = counties[county_idx + 1]
    elif county_idx == len(counties) - 1:
        prev_county = counties[county_idx - 1]
        next_county = None
    else:
        prev_county = counties[county_idx - 1]
        next_county = counties[county_idx + 1]

    # this plots dictionary contains the question and the svg of the q's plot
    question_plots = [{'question': q, 'plot': '<svg' +
                       # four unwanted lines before <svg>; strip them
                       _make_bar_views(q, counties=[county]).split('<svg')[1]}
                      for q in QUESTIONS]

    return render_template("county_plot.html", question_plots=question_plots,
                           county=county, next_county=next_county,
                           prev_county=prev_county)


def _make_bar_views(question, counties=["All"]):
    """
    For now use default of Latah
    """
    sd = SURVEY_DATA
    question_number = QUESTIONS.index(question) + 1
    # take only the data for the particular question
    q_df = sd[sd['question_number'] == question_number]

    # whether or not there are counties, we will need the all-counties frame
    agg_all = q_df.groupby('response').agg({'frequency': np.mean})

    # aggregate (mean of frequencies) over selected counties if any
    if counties != "All":
        agg = q_df[q_df.county.isin(counties)].groupby('response')\
                                              .agg({'frequency': np.mean})

    # put responses in the right order TODO make general for any response set

    # this will make "Strongly Disagree" on bottom and "Strongly Agree" on top
    order = ["Strongly Disagree", "Disagree",
             "Neutral", "Agree", "Strongly Agree"]

    # reorder the aggregated data frame by the order specified
    reindexed = agg.reindex(order)

    # extract responses, used whether or not we have a sub-root collective set
    responses = reindexed.index

    # get collective frequencies of the entire root Palouse region
    all_frequencies = agg_all.reindex(order).frequency

    # return with only root,
    # or also with separate sub-root collective freq and root coll
    if counties == ["All"]:
        # takes responses and corresponding frequencies, order-independent
        return _svg_bar_chart(responses, all_frequencies, title=question)
    else:
        # reorder and select the counties' collective frequencies
        frequencies = reindexed.frequency

        return _svg_bar_chart(responses, all_frequencies, frequencies,
                              label=', '.join(counties), title=question)


def _svg_bar_chart(responses, all_frequencies, frequencies=None,
                   title=None, label=None, svg_dpi=150,
                   xpixels=1100, ypixels=800):
    """
    Create a bar chart with standard matplotlib barh, export as SVG

    Inputs:
        responses, a list of possible survey responses like 'Strongly Agree'
        frequencies, percentage of people giving index-corresponding response

    Returns: An SVG string representation of the bar chart generated by mplib
    """
    fig, ax = plt.subplots(figsize=(xpixels/svg_dpi, ypixels/svg_dpi))

    fmin = 0.0
    fmax = 0.6

    plt.xlim([fmin, fmax])

    response_idx = np.arange(len(responses))

    # plot frequencies and all frequencies
    bar_width = 0.35
    opacity = 0.4

    # plot the Palouse's collective frequency
    plt.barh(response_idx + bar_width, all_frequencies, bar_width,
             color='pink', alpha=opacity, label="All", zorder=10)

    if frequencies is not None:
        # plot the collective frequencies of the selected counties as well
        plt.barh(response_idx, frequencies, bar_width, color='green',
                 alpha=opacity, label=label, zorder=10)

    plt.yticks(response_idx + 0.5, responses, fontsize=14)

    plt.xlabel("Frequency", fontsize=20)

    plt.legend(loc='best', fontsize=16)

    if title is not None:
        plt.title(title, fontsize=23)

    # TODO between one graph and another, there are differences in y axis scale
    # get ymin and ymax as the min and max of the set union of root
    # and sub-root collection frequencies

    plt.tight_layout()

    # see this SO thread: http://tinyurl.com/mn4m83k
    imgdata = StringIO()

    fig.savefig(imgdata, format='svg')
    imgdata.seek(0)

    plt.close()

    return imgdata.buf

if __name__ == '__main__':
    app.run(debug=True)
