/**
 * Thin typed HTTP client for the 1942 Flat Top application API.
 * See docs/design/WEB_ARCHITECTURE.md section 5 for the command/projection contract.
 */
const FlatTopApi = (() => {
  const BASE = '/api';

  async function request(path, options = {}) {
    const response = await fetch(`${BASE}${path}`, {
      headers: { 'Content-Type': 'application/json' },
      ...options,
    });
    if (!response.ok) {
      const detail = await response.text();
      throw new Error(`${response.status} ${response.statusText}: ${detail}`);
    }
    return response.json();
  }

  return {
    listScenarios: () => request('/scenarios'),
    createGame: (scenarioId, playerSide, opponent) =>
      request('/games', {
        method: 'POST',
        body: JSON.stringify({ scenario_id: scenarioId, player_side: playerSide, opponent }),
      }),
    getGame: (gameId, side) => request(`/games/${gameId}?side=${encodeURIComponent(side)}`),
    advancePhase: (gameId, side) =>
      request(`/games/${gameId}/advance-phase?side=${encodeURIComponent(side)}`, { method: 'POST' }),
    movePiece: (gameId, side, pieceId, q, r) =>
      request(`/games/${gameId}/move`, {
        method: 'POST',
        body: JSON.stringify({ side, piece_id: pieceId, q, r }),
      }),
    getReachableHexes: (gameId, pieceId) => request(`/games/${gameId}/units/${encodeURIComponent(pieceId)}/reachable`),
    readinessMove: (gameId, side, baseId, aircraftType, fromStatus, toStatus, count) =>
      request(`/games/${gameId}/air-ops/readiness`, {
        method: 'POST',
        body: JSON.stringify({
          side,
          base_id: baseId,
          aircraft_type: aircraftType,
          from_status: fromStatus,
          to_status: toStatus,
          count,
        }),
      }),
    setArmament: (gameId, side, baseId, aircraftType, armament) =>
      request(`/games/${gameId}/air-ops/armament`, {
        method: 'POST',
        body: JSON.stringify({ side, base_id: baseId, aircraft_type: aircraftType, armament }),
      }),
    createFormation: (gameId, side, baseId, aircraft) =>
      request(`/games/${gameId}/air-ops/formation`, {
        method: 'POST',
        body: JSON.stringify({ side, base_id: baseId, aircraft }),
      }),
  };
})();
