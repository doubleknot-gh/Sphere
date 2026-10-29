'use strict';
// Club names use the same comma separator as the existing member API.
function countMemberships(members) {
  const clubs = new Map();
  const seenMembers = new Set();
  let unassigned = 0;
  for (const member of members) {
    if (seenMembers.has(member.student_id)) continue;
    seenMembers.add(member.student_id);
    const names = new Set((member.club || '').split(',').map(name => name.trim()).filter(Boolean));
    if (!names.size) unassigned++;
    for (const name of names) {
      if (!clubs.has(name)) clubs.set(name, {name, total: 0, active: 0, inactive: 0});
      const club = clubs.get(name);
      club.total++;
      if (member.status === 'active') club.active++;
      else club.inactive++;
    }
  }
  const counts = [...clubs.values()].sort((a, b) => b.total - a.total || a.name.localeCompare(b.name, 'ko'));
  return {clubs: counts, total: counts.reduce((sum, club) => sum + club.total, 0), unassigned};
}
globalThis.SphereClubs = {countMemberships};
if (typeof module !== 'undefined') module.exports = {countMemberships};
