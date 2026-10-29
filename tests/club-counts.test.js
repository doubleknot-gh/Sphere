'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const {countMemberships} = require('../web/club-counts.js');

test('overlapping members count once in each club, with active and inactive subtotals', () => {
  const result = countMemberships([
    {student_id: '1', club: '테니스, 음악', status: 'active'},
    {student_id: '2', club: '테니스', status: 'inactive'},
    {student_id: '3', club: '음악', status: 'active'},
  ]);
  assert.equal(result.total, 4);
  assert.equal(result.unassigned, 0);
  assert.deepEqual(result.clubs.find(club => club.name === '테니스'), {name: '테니스', total: 2, active: 1, inactive: 1});
  assert.deepEqual(result.clubs.find(club => club.name === '음악'), {name: '음악', total: 2, active: 2, inactive: 0});
});

test('repeated clubs, whitespace, duplicate student records and missing clubs do not inflate counts', () => {
  const result = countMemberships([
    {student_id: '1', club: ' 테니스,테니스, , 음악 ', status: 'active'},
    {student_id: '1', club: '테니스, 음악', status: 'active'},
    {student_id: '2', club: null, status: 'active'},
    {student_id: '3', club: ' , ', status: 'inactive'},
  ]);
  assert.equal(result.total, 2);
  assert.equal(result.unassigned, 2);
  assert.equal(result.clubs.length, 2);
  assert.ok(result.clubs.every(club => club.total === 1));
  assert.deepEqual(countMemberships([]), {clubs: [], total: 0, unassigned: 0});
});

test('largest clubs appear first and different club names remain separate', () => {
  const result = countMemberships([
    {student_id: '1', club: 'A, A&B', status: 'active'},
    {student_id: '2', club: 'A&B', status: 'inactive'},
  ]);
  assert.deepEqual(result.clubs.map(club => [club.name, club.total]), [['A&B', 2], ['A', 1]]);
});
