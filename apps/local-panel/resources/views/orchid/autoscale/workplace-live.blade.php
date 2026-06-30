<div id="workplace-live" class="border rounded p-3 bg-body-secondary">
    <div class="mb-2">Состояние: <strong id="fsm-state">Ожидание</strong></div>
    <div class="mb-2">Вес: <strong id="live-weight">—</strong></div>
    <div>Номер: <strong id="live-plate">—</strong></div>
</div>
<p class="text-muted small mt-2 mb-0">Данные обновляются в реальном времени при запущенном workflow.</p>
<script>
(() => {
    const fsmLabels = @json([
        'IDLE' => 'Ожидание',
        'VEHICLE_DETECTED' => 'Авто на весах',
        'PLATE_DETECTING' => 'Распознавание номера',
        'PLATE_CANDIDATE_FOUND' => 'Номер найден',
        'WEIGHT_WAITING' => 'Ожидание веса',
        'WEIGHT_STABILIZING' => 'Стабилизация',
        'READY_TO_CAPTURE' => 'Готово к фиксации',
        'CAPTURED' => 'Зафиксировано',
        'NEED_DRIVER_CREATE' => 'Создать водителя',
        'COMPLETED' => 'Завершено',
    ]);
    const ws = new WebSocket(@json($ws_url));
    ws.onmessage = (e) => {
        const msg = JSON.parse(e.data);
        if (msg.state) {
            document.getElementById('fsm-state').textContent = fsmLabels[msg.state] || msg.state;
        }
        if (msg.weight?.weight != null) {
            const w = Number(msg.weight.weight).toLocaleString('ru-RU');
            document.getElementById('live-weight').textContent = w + ' ' + (msg.weight.unit || 'кг');
        }
        if (msg.plate_candidate?.plate_raw) {
            document.getElementById('live-plate').textContent = msg.plate_candidate.plate_raw;
        }
    };
    ws.onerror = () => {
        document.getElementById('fsm-state').textContent = 'Нет связи с API';
    };
})();
</script>
