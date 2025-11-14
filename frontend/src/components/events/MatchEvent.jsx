/**
 * Match Event Component
 *
 * Displays a tag match event in the event log.
 */
import React from 'react';
import PropTypes from 'prop-types';
import { EVENT_COLORS, EVENT_ICONS } from '../../constants';

const MatchEvent = ({ event, timeStr }) => {
  const colors = EVENT_COLORS.match;

  return (
    <div className={`${colors.bg} border ${colors.border} rounded-lg p-3`}>
      <div className="flex items-start gap-3">
        <div className={`flex-shrink-0 w-8 h-8 bg-yellow-500 rounded-full flex items-center justify-center text-sm`}>
          {EVENT_ICONS.match}
        </div>
        <div className="flex-1 min-w-0">
          <div className={`text-xs ${colors.text} mb-1`}>{timeStr} • Match Found</div>
          <div className="flex flex-wrap gap-1 mt-1">
            {event.matched_tags.map((tag, i) => (
              <span
                key={i}
                className="px-2 py-0.5 bg-yellow-500/20 border border-yellow-500/50 rounded text-xs text-yellow-300"
              >
                {tag}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

MatchEvent.propTypes = {
  event: PropTypes.shape({
    id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
    type: PropTypes.string.isRequired,
    matched_tags: PropTypes.arrayOf(PropTypes.string).isRequired,
    timestamp: PropTypes.number.isRequired,
  }).isRequired,
  timeStr: PropTypes.string.isRequired,
};

export default MatchEvent;
