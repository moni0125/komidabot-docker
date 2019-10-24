from extensions import db
from collections import namedtuple
from typing import Dict, Optional

import komidabot.models as models
from komidabot.users import UserId

_feature = namedtuple('_feature', ['string_id', 'description', 'globally_available', 'active_users'])
_features = [
    _feature('menu_subscription', 'The user can receive a daily menu message automatically', False, [
        # Dev user ID
        UserId('3150885824953769', 'facebook'),
        # Production user IDs
        UserId('1441134665935530', 'facebook'),
        UserId('1532346296833228', 'facebook'),
    ]),
    _feature('new_messaging', 'The user can make use of the new messaging system', False, [
        # Dev user ID
        UserId('3150885824953769', 'facebook'),
        # Production user IDs
        UserId('1441134665935530', 'facebook'),
        UserId('1532346296833228', 'facebook'),
    ]),
]


class _Feature:
    def __init__(self, feat: 'Optional[_feature]', obj: 'Optional[models.Feature]'):
        self.feat = feat
        self.obj = obj

    def __repr__(self):
        return '_Feature({}, {})'.format(repr(self.feat), repr(self.obj))


def update_active_features():
    print('Updating active features', flush=True)

    session = db.session  # FIXME: Create new session

    current_features = models.Feature.get_all()

    feature_mapping = dict()  # type: Dict[str, _Feature]
    for feature in current_features:
        feature_mapping[feature.string_id] = _Feature(None, feature)

    for feature in _features:
        if feature.string_id not in feature_mapping:
            feature_mapping[feature.string_id] = _Feature(feature, None)
        else:
            feature_mapping[feature.string_id].feat = feature

    # print('Features mapping: {}'.format(feature_mapping), flush=True)

    removed_features = [feature.obj for feature in feature_mapping.values() if feature.feat is None]

    for feature in removed_features:  # type: models.Feature
        print('Removing feature {}: {}'.format(feature.string_id, feature.description or 'no description'), flush=True)
        session.delete(feature)

    session.commit()

    new_features = [feature.feat for feature in feature_mapping.values() if feature.obj is None]

    for feature in new_features:  # type: _feature
        print('Adding new feature {}: {}'.format(feature.string_id, feature.description or 'no description'),
              flush=True)
        models.Feature.create(feature.string_id, feature.description, feature.globally_available, session=session)

        for user_id in feature.active_users:  # type: UserId
            user = models.AppUser.find_by_id(user_id.provider, user_id.id)
            if user is None:
                print('Skipping user {}/{} for feature {}'.format(user_id.provider, user_id.id, feature.string_id),
                      flush=True)
                continue
            print('Adding user {}/{} to new feature {}'.format(user_id.provider, user_id.id, feature.string_id),
                  flush=True)
            models.Feature.set_user_participating(user, feature.string_id, True, session=session)

    session.commit()

    existing_features = [feature for feature in feature_mapping.values()
                         if feature.feat is not None and feature.obj is not None]

    for feature in existing_features:  # type: _Feature
        if feature.feat.globally_available != feature.obj.globally_available:
            print('Updating existing feature {}: {}'.format(feature.obj.string_id,
                                                            feature.obj.description or 'no description'), flush=True)
            print('Changing general availability to {}'.format(feature.feat.globally_available), flush=True)

            feature.obj.globally_available = feature.feat.globally_available
        if feature.feat.description != feature.obj.description:
            print('Updating existing feature {}: {}'.format(feature.obj.string_id,
                                                            feature.obj.description or 'no description'), flush=True)
            print('Changing description to {}'.format(feature.feat.description), flush=True)

            feature.obj.description = feature.feat.description

    session.commit()

    print('Done updating active features', flush=True)
