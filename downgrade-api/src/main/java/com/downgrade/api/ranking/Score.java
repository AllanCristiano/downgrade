package com.downgrade.api.ranking;

import jakarta.persistence.*;
import java.time.Instant;

@Entity
@Table(name = "scores", indexes = @Index(name = "idx_scores_level_time", columnList = "level, timeMs"))
public class Score {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 32)
    private String player;

    /** Fase de 1 a 9. */
    @Column(nullable = false)
    private int level;

    /** Tempo para completar a fase, em milissegundos. */
    @Column(nullable = false)
    private long timeMs;

    /** Quantas vezes Marco morreu ate completar a fase. */
    @Column(nullable = false)
    private int deaths;

    @Column(nullable = false)
    private Instant createdAt = Instant.now();

    protected Score() {}

    public Score(String player, int level, long timeMs, int deaths) {
        this.player = player;
        this.level = level;
        this.timeMs = timeMs;
        this.deaths = deaths;
    }

    public Long getId() { return id; }
    public String getPlayer() { return player; }
    public int getLevel() { return level; }
    public long getTimeMs() { return timeMs; }
    public int getDeaths() { return deaths; }
    public Instant getCreatedAt() { return createdAt; }
}
