package com.downgrade.api;

import java.util.Map;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class HealthController {

    private final JdbcTemplate jdbc;

    public HealthController(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    @GetMapping("/api/health")
    public Map<String, Object> health() {
        Integer one = jdbc.queryForObject("SELECT 1", Integer.class);
        return Map.of("status", "ok", "service", "api", "db", one != null && one == 1);
    }
}
