package com.downgrade.api.ranking;

import jakarta.validation.Valid;
import jakarta.validation.constraints.*;
import java.util.List;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/scores")
public class ScoreController {

    public record NewScore(
            @NotBlank @Size(max = 32) String player,
            @Min(1) @Max(9) int level,
            @Positive long timeMs,
            @Min(0) int deaths) {}

    private final ScoreRepository repo;

    public ScoreController(ScoreRepository repo) {
        this.repo = repo;
    }

    /** Ranking (top 10 tempos) de uma fase. */
    @GetMapping("/{level}")
    public List<Score> top(@PathVariable int level) {
        return repo.findTop10ByLevelOrderByTimeMsAsc(level);
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public Score submit(@Valid @RequestBody NewScore body) {
        return repo.save(new Score(body.player(), body.level(), body.timeMs(), body.deaths()));
    }
}
