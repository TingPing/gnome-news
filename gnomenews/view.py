# Copyright (C) 2015 Vadim Rutkovsky <vrutkovs@redhat.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from gi.repository import Gtk, GObject, WebKit2

from gettext import gettext as _

from gnomenews import log
import logging
logger = logging.getLogger(__name__)


class GenericFeedsView(Gtk.Stack):

    __gsignals__ = {
        'open-article': (GObject.SignalFlags.RUN_FIRST, None, (str, str, str, str)),
    }

    @log
    def __init__(self, tracker, name, title=None, show_feedlist=False):
        Gtk.Stack.__init__(self,
                           transition_type=Gtk.StackTransitionType.CROSSFADE)
        self.name = name
        self.title = title

        self.flowbox = Gtk.FlowBox(
            max_children_per_line=2, homogeneous=True,
            activate_on_single_click=True)
        self.flowbox.connect('child-activated', self._post_activated)

        self.feedlist = Gtk.ListBox(activate_on_single_click=True)
        self.feedlist.connect('row-activated', self._feed_activated)

        self._box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        if show_feedlist:
            self._box.pack_start(self.feedlist, True, True, 0)
        self._box.pack_end(self.flowbox, True, True, 0)
        self.add(self._box)

        self.tracker = tracker

        self.show_all()

    @log
    def _add_a_new_preview(self, post):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        title_label = Gtk.Label(label=post["title"])
        box.pack_start(title_label, False, False, 0)

        info_label_text = _("by {0} at {1}".format(
            post['fullname'], post['date'].format('%F %H:%m')))
        info_label = Gtk.Label(label=info_label_text)
        box.pack_start(info_label, False, False, 0)

        webview = WebKit2.WebView()
        webview.load_html(post["content"])
        box.pack_end(webview, True, True, 0)

        #Store the post object to refer to it later on
        box.post = post

        self.flowbox.insert(box, -1)

    @log
    def _add_new_feed(self, feed):
        label = Gtk.Label(label=feed['title'])
        label.channel = feed['channel']
        self.feedlist.insert(label, -1)

    @log
    def _post_activated(self, box, child, user_data=None):
        post = child.get_children()[0].post
        self.emit('open-article',
                  post['title'], post['fullname'], post['url'], post["content"])

    @log
    def _feed_activated(self, box, child, user_data=None):
        [self.flowbox.remove(old_feed) for old_feed in self.flowbox.get_children()]

        urn = child.get_child().channel
        posts = self.tracker.get_posts_for_channel(urn, 10)
        [self._add_a_new_preview(post) for post in posts]
        self.show_all()

    @log
    def update_new_items(self):
        posts = self.tracker.get_post_sorted_by_date(10, unread=True)
        [self._add_a_new_preview(post) for post in posts]
        self.show_all()

    @log
    def update_all_items(self):
        posts = self.tracker.get_post_sorted_by_date(10, unread=False)
        [self._add_a_new_preview(post) for post in posts]
        self.show_all()

    @log
    def update_starred_items(self):
        posts = self.tracker.get_post_sorted_by_date(10, unread=False, starred=True)
        [self._add_a_new_preview(post) for post in posts]
        self.show_all()

    @log
    def update_feeds(self, _=None):
        feeds = self.tracker.get_channels()  # FIXME
        [self._add_new_feed(feed) for feed in feeds]
        self.show_all()


class FeedView(Gtk.Stack):
    def __init__(self, tracker, url, contents):
        Gtk.Stack.__init__(self,
                           transition_type=Gtk.StackTransitionType.CROSSFADE)
        webview = WebKit2.WebView()
        webview.load_html(contents)
        self.add(webview)
        self.show_all()


class NewView(GenericFeedsView):
    def __init__(self, tracker):
        GenericFeedsView.__init__(self, tracker, 'new', _("New"))
        self.update_feeds()


class FeedsView(GenericFeedsView):
    def __init__(self, tracker):
        GenericFeedsView.__init__(self, tracker, 'feeds', _("Feeds"), show_feedlist=True)
        self.update_feeds()


class StarredView(GenericFeedsView):
    def __init__(self, tracker):
        GenericFeedsView.__init__(self, tracker, 'starred', _("Starred"))
        self.update_feeds()


class ReadView(GenericFeedsView):
    def __init__(self, tracker):
        GenericFeedsView.__init__(self, tracker, 'read', _("Read"))
        self.update_starred_items()


class SearchView(GenericFeedsView):
    def __init__(self, tracker):
        GenericFeedsView.__init__(self, tracker, 'search')
