<?php

declare(strict_types=1);

namespace App\Support;

/**
 * Человекочитаемые подписи для demo/panel UI.
 */
final class AutoscaleLabels
{
    private const LICENSE_STATUS = [
        'active' => 'Активна',
        'missing' => 'Не активирована',
        'expired' => 'Истекла',
        'grace' => 'Льготный период',
        'invalid' => 'Недействительна',
        'revoked' => 'Отозвана',
        'machine_mismatch' => 'Другой компьютер',
    ];

    private const WEIGHING_STATUS = [
        'draft' => 'Черновик',
        'completed' => 'Завершено',
        'cancelled' => 'Отменено',
        'need_driver_create' => 'Нужна карточка водителя',
    ];

    private const FSM_STATE = [
        'IDLE' => 'Ожидание',
        'VEHICLE_DETECTED' => 'Авто на весах',
        'PLATE_DETECTING' => 'Распознавание номера',
        'PLATE_CANDIDATE_FOUND' => 'Номер найден',
        'WEIGHT_WAITING' => 'Ожидание веса',
        'WEIGHT_STABILIZING' => 'Стабилизация',
        'READY_TO_CAPTURE' => 'Готово к фиксации',
        'CAPTURED' => 'Зафиксировано',
        'DRIVER_LOOKUP' => 'Поиск водителя',
        'NEED_DRIVER_CREATE' => 'Создать водителя',
        'COMPLETED' => 'Завершено',
        'CANCELLED' => 'Отменено',
        'ERROR' => 'Ошибка',
    ];

    public static function licenseStatus(?string $status): string
    {
        return self::LICENSE_STATUS[$status ?? ''] ?? ($status ?? '—');
    }

    public static function weighingStatus(?string $status): string
    {
        return self::WEIGHING_STATUS[$status ?? ''] ?? ($status ?? '—');
    }

    public static function fsmState(?string $state): string
    {
        return self::FSM_STATE[$state ?? ''] ?? ($state ?? '—');
    }
}
