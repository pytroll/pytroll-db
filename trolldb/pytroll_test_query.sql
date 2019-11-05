select uid from parameter_track where ST_Distance(track, 'POINT(0 47)':: geography) < 100000;
select uid,ST_Length(track)/1000. as track_length from parameter_track;
