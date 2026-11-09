package com.medibot.repository;

import com.medibot.model.DiseaseInfo;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

/**
 * Spring Data JPA Repository for Disease Knowledge Base.
 */
@Repository
public interface DiseaseRepository extends JpaRepository<DiseaseInfo, Long> {

    Optional<DiseaseInfo> findByDiseaseNameIgnoreCase(String diseaseName);

    boolean existsByDiseaseNameIgnoreCase(String diseaseName);
}
