package com.downgrade.api.ranking;

import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ScoreRepository extends JpaRepository<Score, Long> {
    List<Score> findTop10ByLevelOrderByTimeMsAsc(int level);
}
