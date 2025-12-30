"""
텍스트 데이터 청킹(쪼개기) -> 임베딩(벡터로 변환) -> 벡터DB 저장
    - 다중 문서 처리
        - RAG 시스템은 수천, 수만 개의 문서를 다루므로, 문서 간의 검색 격리(Filtering)가 필수
    - 여러 개의 텍스트 파일을 순차적으로 인덱싱하는 구조
    - doc_id 메타데이터를 사용하여 "특정 문서 내"에서만 검색하는 기능 구현
"""

from chromadb.api.types import Document
from chromadb.api.types import Document
import os
import uuid
import chromadb  # 벡터 DB
from chromadb.config import Settings
from sentence_transformers import (
    SentenceTransformer,
)  # 텍스트 - 벡터 변환 (Hugging Face)

# 설정
CHROMA_DB_DIR = "./chroma_db"
COLLECTION_NAME = "rag_collection"
MODEL_NAME = "snunlp/KR-SBERT-V40K-klueNLI-augSTS"

# 1. ChromaDB 클라이언트 초기화 (데이터 디스크 영속 저장)
cilent = chromadb.PersistentClient(path=CHROMA_DB_DIR)

# 2. 컬렉션 생성 또는 로드
collection = cilent.get_or_create_collection(name=COLLECTION_NAME)

# 3. 임베딩 모델 로드
print("임베딩 모델 로드 중...")
model = SentenceTransformer(MODEL_NAME)
print("임베딩 모델 로드 완료...")


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """
    간단한 텍스트 청킹(고정 크기)
        - text: 원본 텍스트 문서
        - chunk_size: 청크 크기(텍스트 분할 크기)
        - overlap: 청크 간 겹치는 구간 크기(문맥 이어지기 위함)
    """
    if overlap >= chunk_size:
        raise ValueError(
            f"overlap 크기({overlap})는 chunk_size({overlap})보다 작아야합니다."
        )

    chunks = []
    start = 0
    text_lens = len(text)

    # 텍스트 문서 끝까지 반복
    while start < text_lens:
        end = min(start + chunk_size, text_lens)
        chunk = text[start:end].strip()  # 시작~끝 크기만큼 텍스트 자르기 및 공백 제거
        if chunk:
            chunks.append(chunk)

        # 끝 부분이 텍스트 문서 끝에 도달하면
        if end == text_lens:
            break

        # 다음 청크 시작부분을 overlap만큼 당겨서 시작(문맥 중간에 잘려도 다음 청크와 문맥 이어지게)
        start = end - overlap

    return chunks


def upsert_document(file_path: str, doc_id: str):
    """
    ChromaDB에 데이터 저장(upsert)
        - 1. 파일 읽기
        - 2. 청킹
        - 3. 기존 doc_id 데이터 삭제 (Idempotency)
        - 4. 임베딩 및 저장
    """
    print(f"\n[{doc_id}] 처리 시작: {file_path}")

    if not os.path.exists(file_path):
        print(f"오류: 파일이 존재하지 않습니다. ({file_path})")
        return

    # 1. 파일 읽기
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()

    # 2. 청킹
    chunks = chunk_text(text)
    print(f"청크 개수: {len(chunks)}")

    # 3. 기존 데이터 삭제(Idempotency)
    existing_count = collection.count()
    collection.delete(where={"doc_id": doc_id})
    print(f"기존 데이터 삭제 완료 (문서 ID: {doc_id})")

    if len(chunks) == 0:
        print("저장할 청크가 없습니다.")
        return

    # 4. 데이터 정보 설정(ids, metadatas)
    ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]  # {문서ID: 순번}
    metadatas = [
        {"doc_id": doc_id, "source": file_path, "chunk_idx": i}
        for i in range(len(chunks))
    ]  # 몇 번째 문서의 몇 번째 조각인지

    # 5. 임베딩 생성 (텍스트 리스트 -> Numpy 벡터 리스트 -> 파이썬 기본 리스트)
    embeddings = model.encode(chunks).tolist()

    # 6. 데이터 저장
    collection.add(
        ids=ids, documents=chunks, metadatas=metadatas, embeddings=embeddings
    )
    current_count = collection.count()
    print(f"[{doc_id}] 저장 완료. (DB 총 청크 수: {current_count})")


def main():
    # 1. 문서 인덱싱
    files_to_index = [
        {"path": "test_doc.txt", "id": "doc_test_001"},
        {"path": "test_doc_2.txt", "id": "doc_cloud_001"},
    ]

    # 2. 문서 청킹 및 DB 저장
    for item in files_to_index:
        upsert_document(item["path"], item["id"])

    # 3. 검색 테스트 (전체 검색 vs 필터링 검색)
    query_text = "gRPC 스트리밍"

    # 쿼리 텍스트를 동일한 모델로 임베딩
    query_vec = model.encode([query_text]).tolist()

    print(f"\n===== 검색 테스트: '{query_text}' =====")

    # ===== Case A: 전체 검색 (필터 없음) =====
    print("\n[Case A] 전체 검색 (모든 문서 대상)")

    # 벡터 변환된 질문 -> 유사도 비교 -> 가장 유사도가 높은 상위 3개 결과
    results_all = collection.query(query_embeddings=query_vec, n_results=3)

    # collection.query()는 질문을 여러 개([질문1, 질문2, ...]) 받을 수 있어,
    # 결과도 이중 리스트([[결과1, 결과2...], [결과1, 결과2...]]) 형태로 반환
    # 질문을 1개만 던졌으므로 첫 번째 질문의 결과인 0번 인덱스 리스트 추출
    for i, doc in enumerate[Document](results_all["documents"][0]):
        # ChromaDB는 documents 리스트와 metadatas 리스트의 순서를 동일하게 보장하므로
        # i번째 documents에 맞는 i번째 metadatas 추출
        meta = results_all["metadatas"][0][i]

        # i번째 유사도 거리(distance, 작을수록 유사도 높음)
        dist = results_all["distances"][0][i]

        print(f" - [거리: {dist:.4f}] [{meta['doc_id']}] {doc[:50]}...")

    # ===== Case B: 필터링 검색 (특정 문서만 대상) =====
    target_doc = "doc_cloud_001"
    print(f"\n[Case B] 필터링 검색 (대상: {target_doc} 만)")

    # 벡터 변환된 질문 -> 메터데이터 필터링 -> 유사도 비교 -> 가장 유사도가 높은 상위 3개 결과
    results_filtered = collection.query(
        query_embeddings=query_vec, n_results=3, where={"doc_id": target_doc}
    )

    if not results_filtered["documents"][0]:
        print("검색 결과 없음.")
    else:
        for i, doc in enumerate[Document](results_filtered["documents"][0]):
            meta = results_filtered["metadatas"][0][i]
            dist = results_all["distances"][0][i]
            print(f" - [거리: {dist:.4f}] [{meta['doc_id']}] {doc[:50]}...")


if __name__ == "__main__":
    main()
