<?php

declare(strict_types=1);

namespace App\Support;

use Orchid\Screen\Repository;

/**
 * Преобразует строки из local-api в Orchid Repository для Layout::table.
 */
final class OrchidRows
{
    /**
     * @param  list<array<string, mixed>>  $rows
     * @return list<Repository>
     */
    public static function fromArrays(array $rows): array
    {
        return array_map(
            static fn (array $row): Repository => new Repository($row),
            $rows
        );
    }
}
