<?php

declare(strict_types=1);

namespace App\Orchid\Screens;

use App\Services\LocalApiClient;
use Illuminate\Http\Request;
use Orchid\Screen\Actions\Button;
use Orchid\Screen\Fields\Input;
use Orchid\Screen\Fields\Select;
use Orchid\Screen\Screen;
use Orchid\Support\Facades\Layout;
use Orchid\Support\Facades\Toast;

class TerminalEditScreen extends Screen
{
    public function __construct(private readonly LocalApiClient $api) {}

    public function query(): iterable
    {
        return [
            'terminal' => [
                'name' => '',
                'driver_type' => 'demo',
                'config' => [],
            ],
        ];
    }

    public function name(): ?string
    {
        return 'Новый терминал';
    }

    public function commandBar(): iterable
    {
        return [
            Button::make('Проверить подключение')->method('testConnection')->icon('bs.plug'),
            Button::make('Сохранить')->method('save')->class('btn btn-primary'),
        ];
    }

    public function layout(): iterable
    {
        return [
            Layout::rows([
                Input::make('terminal.name')->title('Название')->required(),
                Select::make('terminal.driver_type')->title('Тип')->options([
                    'demo' => 'DEMO',
                    'keli_d2008fa' => 'Keli D2008FA',
                    'cas_ci200a' => 'CAS CI-200A',
                ]),
                Input::make('terminal.config.port')->title('COM-порт')->help('Например COM1'),
                Input::make('terminal.config.baudrate')->title('Скорость')->value(9600),
                Select::make('terminal.config.parity')->title('Чётность')->options([
                    'none' => 'none',
                    'even' => 'even',
                    'odd' => 'odd',
                ])->value('none'),
                Input::make('terminal.config.timeout')->title('Таймаут (с)')->type('number')->value(2),
            ]),
        ];
    }

    private function terminalPayload(Request $request): array
    {
        $data = $request->get('terminal', []);
        $config = array_filter([
            'port' => $data['config']['port'] ?? null,
            'baudrate' => isset($data['config']['baudrate']) ? (int) $data['config']['baudrate'] : null,
            'parity' => $data['config']['parity'] ?? null,
            'timeout' => isset($data['config']['timeout']) ? (float) $data['config']['timeout'] : null,
        ], static fn ($value) => $value !== null && $value !== '');

        return [
            'name' => $data['name'] ?? 'Terminal',
            'driver_type' => $data['driver_type'] ?? 'demo',
            'config' => $config,
        ];
    }

    public function testConnection(Request $request): void
    {
        try {
            $terminal = $this->api->post('/api/terminals', $this->terminalPayload($request));
            $result = $this->api->post('/api/terminals/'.$terminal['id'].'/test');
            $reading = $result['sample_reading'] ?? null;
            $hasValidReading = is_array($reading)
                && ($reading['status'] ?? 'ok') === 'ok'
                && empty($reading['error']);
            $success = (bool) ($result['success'] ?? false);
            $connected = (bool) ($result['connected'] ?? false);
            if ($success && $hasValidReading) {
                $connected = true;
            }

            if (! $success) {
                $code = $result['error_code'] ?? 'error';
                $message = $result['message'] ?? 'Проверка не удалась';
                $raw = is_array($reading) ? ($reading['raw'] ?? '') : '';
                Toast::error($this->formatTestError($connected, $code, $message, $raw));

                return;
            }

            if (is_array($reading)) {
                Toast::success($this->formatTestSuccess($reading, $connected));
            } else {
                Toast::success($result['message'] ?? 'Подключение успешно');
            }
        } catch (\Throwable $e) {
            Toast::error($e->getMessage());
        }
    }

    private function formatTestSuccess(array $reading, bool $connected): string
    {
        $weight = $reading['weight'] ?? '—';
        $unit = $reading['unit'] ?? 'кг';
        $stable = ($reading['stable'] ?? false) ? 'да' : 'нет';
        $raw = $reading['raw'] ?? '';

        return sprintf(
            'Подключение успешно. Вес: %s %s. Стабильный: %s. Raw: %s',
            $weight,
            $unit,
            $stable,
            $raw
        );
    }

    private function formatTestError(bool $connected, string $code, string $message, string $raw): string
    {
        $prefix = $connected ? 'COM открыт, но проверка не удалась' : 'Подключение не удалось';

        return $raw !== ''
            ? sprintf('%s (%s): %s. Raw: %s', $prefix, $code, $message, $raw)
            : sprintf('%s (%s): %s', $prefix, $code, $message);
    }

    public function save(Request $request): \Illuminate\Http\RedirectResponse
    {
        try {
            $this->api->post('/api/terminals', $this->terminalPayload($request));
            Toast::success('Терминал создан');
        } catch (\Throwable $e) {
            Toast::error($e->getMessage());
        }

        return redirect()->route('platform.terminals');
    }
}
